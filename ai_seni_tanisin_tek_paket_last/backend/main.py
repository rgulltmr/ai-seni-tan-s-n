import os
import uuid
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
import qrcode
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# AYARLAR
# =========================================================
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

OUTPUT_DIR = Path("generated")
PDF_DIR = OUTPUT_DIR / "pdfs"
QR_DIR = OUTPUT_DIR / "qrs"

PDF_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = os.getenv("PDF_FONT_PATH")
FONT_NAME = "Helvetica"

if FONT_PATH and Path(FONT_PATH).exists():
    pdfmetrics.registerFont(TTFont("CustomFont", FONT_PATH))
    FONT_NAME = "CustomFont"

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1/chat/completions")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen3.5-9b")

LOGO_PATH = Path(__file__).resolve().parent / "logo2.png"

# =========================================================
# FASTAPI
# =========================================================
app = FastAPI(title="AI Knows You - Local Hybrid AI", version="9.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated", StaticFiles(directory=str(OUTPUT_DIR)), name="generated")

# =========================================================
# SORULAR
# =========================================================
QuestionId = Literal["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]

QUESTIONS = [
    {
        "id": "q1",
        "question": "Yeni bir ortamda nasıl davranırsın?",
        "options": [
            "Önce gözlemlerim, sonra hareket ederim.",
            "İnsanlarla hızlıca iletişim kurarım.",
            "Kendi akışımda ilerlemeyi tercih ederim.",
            "Duruma göre değişir.",
        ],
    },
    {
        "id": "q2",
        "question": "Bir problemle karşılaştığında ilk tepkin nedir?",
        "options": [
            "Önce durumu analiz ederim.",
            "Hızlı bir çözüm denerim.",
            "Başkalarının görüşünü alırım.",
            "Farklı fikirler üretmeyi denerim.",
        ],
    },
    {
        "id": "q3",
        "question": "Seni en çok ne motive eder?",
        "options": [
            "Başarı ve ilerleme hissi.",
            "Maddi kazanç.",
            "İnsanlar üzerinde olumlu etki bırakmak.",
            "Özgür olmak.",
        ],
    },
    {
        "id": "q4",
        "question": "Nasıl çalışmayı tercih edersin?",
        "options": [
            "Tek başıma.",
            "Küçük bir ekiple.",
            "Kalabalık bir ekip içinde.",
            "Duruma göre değişir.",
        ],
    },
    {
        "id": "q5",
        "question": "Karar verirken en çok neye güvenirsin?",
        "options": [
            "Mantığıma.",
            "Sezgilerime.",
            "Geçmiş deneyimlerime.",
            "Başkalarının görüşlerine.",
        ],
    },
    {
        "id": "q6",
        "question": "Hangi çalışma tarzı sana daha yakın?",
        "options": [
            "Planlı ilerlemek.",
            "Esnek ilerlemek.",
            "Risk alarak ilerlemek.",
            "Güvende kalmak.",
        ],
    },
    {
        "id": "q7",
        "question": "Kendini en çok hangi rolde görüyorsun?",
        "options": [
            "Lider.",
            "Uzman.",
            "Üreten ve geliştiren.",
            "Destekleyici ve dengeleyici.",
        ],
    },
    {
        "id": "q8",
        "question": "Gelecekte kendini nerede görmek isterdin?",
        "options": [
            "Daha fazla sorumluluk alan biri olarak.",
            "Belirli bir alanda uzman biri olarak.",
            "Yeni şeyler deneyen biri olarak.",
            "Henüz emin değilim.",
        ],
    },
]

OPTION_INDEX = {q["id"]: {i: opt for i, opt in enumerate(q["options"])} for q in QUESTIONS}

# =========================================================
# MODELLER
# =========================================================
class AnswerItem(BaseModel):
    question_id: QuestionId
    selected_index: int = Field(ge=0, le=3)


class AnalyzeRequest(BaseModel):
    name: Optional[str] = "Katılımcı"
    answers: List[AnswerItem]

# =========================================================
# PUANLAMA
# =========================================================
def create_empty_scores() -> Dict[str, Dict[str, int]]:
    return {
        "social": {
            "introvert": 0,
            "extrovert": 0,
            "balanced": 0,
        },
        "decision": {
            "analytic": 0,
            "intuitive": 0,
            "experience": 0,
            "collaborative": 0,
            "action": 0,
            "creative": 0,
        },
        "motivation": {
            "success": 0,
            "money": 0,
            "impact": 0,
            "freedom": 0,
            "growth": 0,
            "exploration": 0,
            "stability": 0,
        },
        "work_style": {
            "independent": 0,
            "team": 0,
            "flexible": 0,
            "structured": 0,
            "adaptive": 0,
        },
        "role": {
            "leader": 0,
            "expert": 0,
            "creator": 0,
            "support": 0,
        },
    }


def score_answers(answers: List[AnswerItem]) -> Dict[str, Dict[str, int]]:
    scores = create_empty_scores()

    for item in answers:
        qid = item.question_id
        idx = item.selected_index

        if qid == "q1":
            if idx == 0:
                scores["social"]["introvert"] += 2
                scores["decision"]["analytic"] += 1
            elif idx == 1:
                scores["social"]["extrovert"] += 2
                scores["role"]["leader"] += 1
            elif idx == 2:
                scores["social"]["introvert"] += 2
                scores["work_style"]["independent"] += 1
            elif idx == 3:
                scores["social"]["balanced"] += 2
                scores["work_style"]["adaptive"] += 1

        elif qid == "q2":
            if idx == 0:
                scores["decision"]["analytic"] += 2
                scores["role"]["expert"] += 1
            elif idx == 1:
                scores["decision"]["action"] += 2
                scores["role"]["leader"] += 1
            elif idx == 2:
                scores["decision"]["collaborative"] += 2
                scores["work_style"]["team"] += 1
            elif idx == 3:
                scores["decision"]["creative"] += 2
                scores["role"]["creator"] += 1

        elif qid == "q3":
            if idx == 0:
                scores["motivation"]["success"] += 3
                scores["motivation"]["growth"] += 1
            elif idx == 1:
                scores["motivation"]["money"] += 3
            elif idx == 2:
                scores["motivation"]["impact"] += 3
                scores["role"]["leader"] += 1
            elif idx == 3:
                scores["motivation"]["freedom"] += 3
                scores["role"]["creator"] += 1

        elif qid == "q4":
            if idx == 0:
                scores["work_style"]["independent"] += 3
                scores["social"]["introvert"] += 1
            elif idx == 1:
                scores["work_style"]["team"] += 2
                scores["social"]["balanced"] += 1
            elif idx == 2:
                scores["work_style"]["team"] += 3
                scores["social"]["extrovert"] += 1
            elif idx == 3:
                scores["work_style"]["flexible"] += 3
                scores["work_style"]["adaptive"] += 1

        elif qid == "q5":
            if idx == 0:
                scores["decision"]["analytic"] += 3
            elif idx == 1:
                scores["decision"]["intuitive"] += 3
            elif idx == 2:
                scores["decision"]["experience"] += 3
            elif idx == 3:
                scores["decision"]["collaborative"] += 3

        elif qid == "q6":
            if idx == 0:
                scores["work_style"]["structured"] += 3
                scores["motivation"]["stability"] += 1
            elif idx == 1:
                scores["work_style"]["flexible"] += 2
                scores["work_style"]["adaptive"] += 1
            elif idx == 2:
                scores["motivation"]["exploration"] += 2
                scores["role"]["leader"] += 1
                scores["role"]["creator"] += 1
            elif idx == 3:
                scores["motivation"]["stability"] += 2
                scores["role"]["expert"] += 1

        elif qid == "q7":
            if idx == 0:
                scores["role"]["leader"] += 4
            elif idx == 1:
                scores["role"]["expert"] += 4
            elif idx == 2:
                scores["role"]["creator"] += 4
            elif idx == 3:
                scores["role"]["support"] += 4

        elif qid == "q8":
            if idx == 0:
                scores["motivation"]["success"] += 2
                scores["role"]["leader"] += 1
            elif idx == 1:
                scores["motivation"]["growth"] += 2
                scores["role"]["expert"] += 1
            elif idx == 2:
                scores["motivation"]["exploration"] += 2
                scores["role"]["creator"] += 1
            elif idx == 3:
                scores["work_style"]["adaptive"] += 1
                scores["social"]["balanced"] += 1

    return scores


def winner(score_dict: Dict[str, int]) -> str:
    return max(score_dict, key=score_dict.get)


def build_profile(scores: Dict[str, Dict[str, int]]) -> Dict[str, str]:
    label_maps = {
        "social": {
            "introvert": "İçe dönük",
            "extrovert": "Dışa dönük",
            "balanced": "Dengeli",
        },
        "decision": {
            "analytic": "Analitik",
            "intuitive": "Sezgisel",
            "experience": "Deneyim temelli",
            "collaborative": "İş birliğine açık",
            "action": "Aksiyon odaklı",
            "creative": "Yaratıcı",
        },
        "motivation": {
            "success": "Başarı odaklı",
            "money": "Maddi kazanç odaklı",
            "impact": "Etki odaklı",
            "freedom": "Özgürlük odaklı",
            "growth": "Gelişim odaklı",
            "exploration": "Keşif odaklı",
            "stability": "Güvenlik odaklı",
        },
        "work_style": {
            "independent": "Bağımsız",
            "team": "Takım odaklı",
            "flexible": "Esnek",
            "structured": "Planlı",
            "adaptive": "Uyumlu",
        },
        "role": {
            "leader": "Lider",
            "expert": "Uzman",
            "creator": "Üreten/Geliştiren",
            "support": "Destekleyici",
        },
    }

    return {
        "social": label_maps["social"][winner(scores["social"])],
        "decision": label_maps["decision"][winner(scores["decision"])],
        "motivation": label_maps["motivation"][winner(scores["motivation"])],
        "work_style": label_maps["work_style"][winner(scores["work_style"])],
        "role": label_maps["role"][winner(scores["role"])],
    }


def answers_to_text_map(answers: List[AnswerItem]) -> Dict[str, str]:
    return {
        item.question_id: OPTION_INDEX[item.question_id][item.selected_index]
        for item in answers
    }

# =========================================================
# KURAL TABANLI METİNLER
# =========================================================
def build_super_power(profile: Dict[str, str]) -> str:
    decision = profile["decision"]
    role = profile["role"]
    work_style = profile["work_style"]

    if decision == "Analitik" and role == "Uzman":
        return "Gücün, karmaşık durumları analiz edip sağlam kararlar verebilmen."
    if role == "Lider" and profile["motivation"] == "Etki odaklı":
        return "Gücün, insanları ortak bir amaç etrafında bir araya getirip yönlendirebilmen."
    if role == "Üreten/Geliştiren" and decision == "Yaratıcı":
        return "Gücün, yeni fikirleri somut ve uygulanabilir sonuçlara dönüştürebilmen."
    if work_style == "Bağımsız":
        return "Gücün, tek başına odaklanıp işi sonuna kadar sürdürebilmen."
    if work_style == "Takım odaklı":
        return "Gücün, başkalarıyla birlikte düzen kurup değer üretebilmen."
    return "Gücün, dengeli ve düşünülmüş bir şekilde ilerleyebilmen."


def build_blocking_point(profile: Dict[str, str]) -> str:
    social = profile["social"]
    work_style = profile["work_style"]
    decision = profile["decision"]
    motivation = profile["motivation"]

    if social == "İçe dönük":
        return "Bazen geri planda kalman, güçlü yönlerinin fark edilmesini geciktirebilir."
    if decision == "Analitik":
        return "Bazen fazla düşünmek, karar alma hızını yavaşlatabilir."
    if work_style == "Bağımsız":
        return "Her şeyi tek başına üstlenmek, gerektiğinde destek istemeni zorlaştırabilir."
    if motivation == "Başarı odaklı":
        return "Kendinden yüksek beklenti içinde olman zaman zaman gereksiz baskı oluşturabilir."
    return "Bazen fazla temkinli olmak, potansiyelinin daha geç görünmesine neden olabilir."


def build_career_suggestions(profile: Dict[str, str]) -> List[str]:
    role = profile["role"]
    decision = profile["decision"]
    motivation = profile["motivation"]
    work_style = profile["work_style"]

    suggestions = []

    if role == "Uzman" and decision == "Analitik":
        suggestions.extend(["Veri", "Araştırma", "Teknoloji"])

    if role == "Lider" and motivation in ["Başarı odaklı", "Etki odaklı"]:
        suggestions.extend(["Yönetim", "Operasyon", "Strateji"])

    if role == "Üreten/Geliştiren":
        suggestions.extend(["Tasarım", "Medya", "Ürün geliştirme"])

    if work_style == "Takım odaklı":
        suggestions.extend(["Danışmanlık", "İnsan ilişkileri", "İletişim"])

    if motivation == "Özgürlük odaklı":
        suggestions.extend(["Girişimcilik", "Yaratıcı işler", "Ürün geliştirme"])

    defaults = ["İş geliştirme", "Eğitim", "Araştırma"]

    merged = suggestions + defaults
    unique = []
    for item in merged:
        if item not in unique:
            unique.append(item)

    return unique[:4]

# =========================================================
# MESLEK HAVUZU
# =========================================================
JOB_CATALOG = [
    {"title": "Proje Yöneticisi", "field": "Yönetim", "role": ["Lider"], "decision": ["Analitik", "Aksiyon odaklı", "İş birliğine açık"], "motivation": ["Başarı odaklı", "Etki odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Operasyon Yöneticisi", "field": "Yönetim", "role": ["Lider"], "decision": ["Aksiyon odaklı", "Analitik"], "motivation": ["Başarı odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Ekip Lideri", "field": "Yönetim", "role": ["Lider"], "decision": ["Aksiyon odaklı", "İş birliğine açık"], "motivation": ["Başarı odaklı", "Etki odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Program Koordinatörü", "field": "Yönetim", "role": ["Lider", "Destekleyici"], "decision": ["İş birliğine açık", "Analitik"], "motivation": ["Etki odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "İdari İşler Yöneticisi", "field": "Yönetim", "role": ["Lider", "Destekleyici"], "decision": ["Deneyim temelli", "Analitik"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["Dengeli"]},

    {"title": "İş Analisti", "field": "İş", "role": ["Uzman", "Lider"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Strateji Analisti", "field": "İş", "role": ["Uzman"], "decision": ["Analitik"], "motivation": ["Gelişim odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "İş Geliştirme Uzmanı", "field": "İş", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Aksiyon odaklı", "İş birliğine açık"], "motivation": ["Başarı odaklı", "Gelişim odaklı"], "work_style": ["Esnek", "Takım odaklı"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "İş Ortaklıkları Yöneticisi", "field": "İş", "role": ["Lider"], "decision": ["İş birliğine açık", "Aksiyon odaklı"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük"]},
    {"title": "Danışman", "field": "İş", "role": ["Uzman", "Lider"], "decision": ["Analitik", "İş birliğine açık"], "motivation": ["Gelişim odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},

    {"title": "Veri Analisti", "field": "Veri", "role": ["Uzman"], "decision": ["Analitik"], "motivation": ["Gelişim odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "İş Zekâsı Analisti", "field": "Veri", "role": ["Uzman"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Raporlama Uzmanı", "field": "Veri", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Pazar Araştırma Analisti", "field": "Veri", "role": ["Uzman"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı", "Etki odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Veri Operasyon Uzmanı", "field": "Veri", "role": ["Destekleyici", "Uzman"], "decision": ["Analitik"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["İçe dönük", "Dengeli"]},

    {"title": "Yazılım Geliştirici", "field": "Teknoloji", "role": ["Uzman", "Üreten/Geliştiren"], "decision": ["Analitik", "Yaratıcı"], "motivation": ["Gelişim odaklı", "Özgürlük odaklı"], "work_style": ["Bağımsız", "Planlı"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Frontend Geliştirici", "field": "Teknoloji", "role": ["Üreten/Geliştiren", "Uzman"], "decision": ["Yaratıcı", "Analitik"], "motivation": ["Gelişim odaklı", "Özgürlük odaklı"], "work_style": ["Bağımsız", "Esnek"], "social": ["Dengeli"]},
    {"title": "Backend Geliştirici", "field": "Teknoloji", "role": ["Uzman"], "decision": ["Analitik"], "motivation": ["Gelişim odaklı"], "work_style": ["Bağımsız", "Planlı"], "social": ["İçe dönük"]},
    {"title": "Kalite Güvence Uzmanı", "field": "Teknoloji", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Güvenlik odaklı", "Gelişim odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Sistem Uzmanı", "field": "Teknoloji", "role": ["Uzman"], "decision": ["Analitik", "Aksiyon odaklı"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["Dengeli"]},
    {"title": "Teknik Destek Uzmanı", "field": "Teknoloji", "role": ["Destekleyici"], "decision": ["İş birliğine açık", "Aksiyon odaklı"], "motivation": ["Etki odaklı", "Güvenlik odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dengeli", "Dışa dönük"]},

    {"title": "UX/UI Tasarımcısı", "field": "Tasarım", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı", "Sezgisel"], "motivation": ["Özgürlük odaklı", "Etki odaklı"], "work_style": ["Esnek", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Ürün Tasarımcısı", "field": "Tasarım", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı", "Analitik"], "motivation": ["Etki odaklı", "Özgürlük odaklı"], "work_style": ["Esnek", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Grafik Tasarımcı", "field": "Tasarım", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı"], "motivation": ["Özgürlük odaklı"], "work_style": ["Esnek", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Görsel Tasarımcı", "field": "Tasarım", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı", "Sezgisel"], "motivation": ["Özgürlük odaklı", "Etki odaklı"], "work_style": ["Bağımsız", "Esnek"], "social": ["Dengeli"]},
    {"title": "Motion Designer", "field": "Tasarım", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı"], "motivation": ["Özgürlük odaklı", "Gelişim odaklı"], "work_style": ["Esnek"], "social": ["Dengeli"]},
    {"title": "Sanat Direktörü", "field": "Tasarım", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Yaratıcı", "İş birliğine açık"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Takım odaklı", "Esnek"], "social": ["Dengeli", "Dışa dönük"]},

    {"title": "İçerik Üreticisi", "field": "Medya", "role": ["Üreten/Geliştiren"], "decision": ["Yaratıcı", "Sezgisel"], "motivation": ["Özgürlük odaklı", "Etki odaklı"], "work_style": ["Esnek"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Metin Yazarı", "field": "Medya", "role": ["Üreten/Geliştiren", "Uzman"], "decision": ["Yaratıcı", "Sezgisel"], "motivation": ["Etki odaklı", "Özgürlük odaklı"], "work_style": ["Bağımsız", "Esnek"], "social": ["Dengeli"]},
    {"title": "Editör", "field": "Medya", "role": ["Uzman", "Üreten/Geliştiren"], "decision": ["Analitik", "Yaratıcı"], "motivation": ["Gelişim odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Sosyal Medya Uzmanı", "field": "Medya", "role": ["Üreten/Geliştiren", "Lider"], "decision": ["Yaratıcı", "Aksiyon odaklı"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Esnek", "Uyumlu"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "İçerik Stratejisti", "field": "Medya", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Yaratıcı", "Analitik"], "motivation": ["Etki odaklı", "Gelişim odaklı"], "work_style": ["Planlı", "Esnek"], "social": ["Dengeli"]},

    {"title": "Pazarlama Uzmanı", "field": "Pazarlama", "role": ["Üreten/Geliştiren", "Lider"], "decision": ["Yaratıcı", "İş birliğine açık"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Takım odaklı", "Esnek"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Marka Stratejisti", "field": "Pazarlama", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Yaratıcı", "Analitik"], "motivation": ["Etki odaklı"], "work_style": ["Esnek", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Dijital Pazarlama Uzmanı", "field": "Pazarlama", "role": ["Üreten/Geliştiren", "Uzman"], "decision": ["Analitik", "Yaratıcı"], "motivation": ["Başarı odaklı", "Gelişim odaklı"], "work_style": ["Esnek", "Planlı"], "social": ["Dengeli"]},
    {"title": "SEO Uzmanı", "field": "Pazarlama", "role": ["Uzman"], "decision": ["Analitik"], "motivation": ["Gelişim odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Kampanya Yöneticisi", "field": "Pazarlama", "role": ["Lider"], "decision": ["Aksiyon odaklı", "İş birliğine açık"], "motivation": ["Başarı odaklı", "Etki odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük", "Dengeli"]},

    {"title": "İnsan Kaynakları Uzmanı", "field": "İnsan", "role": ["Destekleyici", "Lider"], "decision": ["İş birliğine açık", "Deneyim temelli"], "motivation": ["Etki odaklı", "Güvenlik odaklı"], "work_style": ["Takım odaklı", "Planlı"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "İşe Alım Uzmanı", "field": "İnsan", "role": ["Destekleyici", "Lider"], "decision": ["İş birliğine açık", "Aksiyon odaklı"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Takım odaklı", "Esnek"], "social": ["Dışa dönük"]},
    {"title": "Müşteri Başarı Uzmanı", "field": "İnsan", "role": ["Destekleyici"], "decision": ["İş birliğine açık", "Deneyim temelli"], "motivation": ["Etki odaklı", "Güvenlik odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "İletişim Uzmanı", "field": "İnsan", "role": ["Destekleyici", "Üreten/Geliştiren"], "decision": ["İş birliğine açık", "Yaratıcı"], "motivation": ["Etki odaklı"], "work_style": ["Takım odaklı", "Esnek"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Topluluk Yöneticisi", "field": "İnsan", "role": ["Destekleyici", "Lider"], "decision": ["İş birliğine açık", "Aksiyon odaklı"], "motivation": ["Etki odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük"]},

    {"title": "Eğitmen", "field": "Eğitim", "role": ["Destekleyici", "Uzman"], "decision": ["İş birliğine açık", "Deneyim temelli"], "motivation": ["Etki odaklı", "Gelişim odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Eğitim Uzmanı", "field": "Eğitim", "role": ["Destekleyici", "Uzman"], "decision": ["Deneyim temelli", "İş birliğine açık"], "motivation": ["Etki odaklı"], "work_style": ["Planlı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Öğretim Tasarımcısı", "field": "Eğitim", "role": ["Üreten/Geliştiren", "Uzman"], "decision": ["Yaratıcı", "Analitik"], "motivation": ["Etki odaklı", "Gelişim odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["Dengeli"]},
    {"title": "Akademik Danışman", "field": "Eğitim", "role": ["Destekleyici"], "decision": ["İş birliğine açık", "Deneyim temelli"], "motivation": ["Etki odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},

    {"title": "Araştırma Uzmanı", "field": "Araştırma", "role": ["Uzman"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı"], "work_style": ["Bağımsız", "Planlı"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Araştırma Asistanı", "field": "Araştırma", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı"], "work_style": ["Bağımsız", "Planlı"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Kalite Uzmanı", "field": "Araştırma", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["İçe dönük"]},
    {"title": "Uyum Uzmanı", "field": "Araştırma", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["Dengeli"]},

    {"title": "Ürün Yöneticisi", "field": "Ürün", "role": ["Lider", "Uzman"], "decision": ["Analitik", "İş birliğine açık"], "motivation": ["Etki odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Ürün Uzmanı", "field": "Ürün", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Gelişim odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Uyumlu"], "social": ["Dengeli"]},
    {"title": "Ürün Operasyon Uzmanı", "field": "Ürün", "role": ["Destekleyici", "Lider"], "decision": ["Analitik", "Aksiyon odaklı"], "motivation": ["Başarı odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli"]},
    {"title": "Girişimci", "field": "Girişimcilik", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Yaratıcı", "Aksiyon odaklı", "Sezgisel"], "motivation": ["Özgürlük odaklı", "Başarı odaklı"], "work_style": ["Esnek", "Uyumlu"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Startup Kurucusu", "field": "Girişimcilik", "role": ["Lider", "Üreten/Geliştiren"], "decision": ["Aksiyon odaklı", "Yaratıcı"], "motivation": ["Özgürlük odaklı", "Başarı odaklı"], "work_style": ["Uyumlu", "Esnek"], "social": ["Dışa dönük", "Dengeli"]},
    {"title": "Serbest Çalışan Uzman", "field": "Girişimcilik", "role": ["Üreten/Geliştiren", "Uzman"], "decision": ["Yaratıcı", "Sezgisel"], "motivation": ["Özgürlük odaklı"], "work_style": ["Bağımsız", "Esnek"], "social": ["İçe dönük", "Dengeli"]},

    {"title": "Finans Analisti", "field": "Finans", "role": ["Uzman"], "decision": ["Analitik"], "motivation": ["Başarı odaklı", "Güvenlik odaklı"], "work_style": ["Planlı", "Bağımsız"], "social": ["İçe dönük", "Dengeli"]},
    {"title": "Bütçe Planlama Uzmanı", "field": "Finans", "role": ["Uzman", "Destekleyici"], "decision": ["Analitik", "Deneyim temelli"], "motivation": ["Güvenlik odaklı"], "work_style": ["Planlı"], "social": ["Dengeli"]},
    {"title": "Satın Alma Uzmanı", "field": "Finans", "role": ["Destekleyici", "Lider"], "decision": ["Analitik", "İş birliğine açık"], "motivation": ["Güvenlik odaklı", "Başarı odaklı"], "work_style": ["Planlı", "Takım odaklı"], "social": ["Dengeli"]},

    {"title": "STK Proje Sorumlusu", "field": "Sosyal Etki", "role": ["Destekleyici", "Lider"], "decision": ["İş birliğine açık", "Deneyim temelli"], "motivation": ["Etki odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dengeli", "Dışa dönük"]},
    {"title": "Sosyal Projeler Koordinatörü", "field": "Sosyal Etki", "role": ["Lider", "Destekleyici"], "decision": ["İş birliğine açık", "Aksiyon odaklı"], "motivation": ["Etki odaklı"], "work_style": ["Takım odaklı", "Uyumlu"], "social": ["Dışa dönük", "Dengeli"]},
]


def score_job(profile: Dict[str, str], job: Dict[str, object]) -> int:
    score = 0
    if profile["role"] in job["role"]:
        score += 4
    if profile["decision"] in job["decision"]:
        score += 3
    if profile["motivation"] in job["motivation"]:
        score += 3
    if profile["work_style"] in job["work_style"]:
        score += 2
    if profile["social"] in job["social"]:
        score += 1
    return score


def build_best_job_suggestion(profile: Dict[str, str]) -> str:
    scored_jobs = []

    for job in JOB_CATALOG:
        score = score_job(profile, job)
        if score > 0:
            scored_jobs.append((job["title"], score))

    if not scored_jobs:
        return "İş Analisti"

    scored_jobs.sort(key=lambda x: x[1], reverse=True)
    return scored_jobs[0][0]

# =========================================================
# YAPAY ZEKA METİN ÜRETİMİ
# =========================================================
def call_local_ai_summary_and_story(name: str, profile: Dict[str, str], answer_texts: Dict[str, str]) -> Dict[str, str]:
    prompt = f"""
Sadece geçerli JSON döndür.

Kurallar:
- Doğal ve akıcı Türkçe kullan.
- Cümleler kısa ve anlaşılır olsun.
- Garip, yapay veya aşırı abartılı ifadeler kullanma.
- Kırıcı, uygunsuz veya olumsuz yargılayıcı dil kullanma.
- short_summary en az 3 cümle en fazla 5 cümle olsun.
- five_year_story en az 4 cümle en fazla 6 cümle olsun.
- Ton sıcak, gerçekçi ve anlaşılır olsun.

JSON formatı:
{{
  "short_summary": "",
  "five_year_story": ""
}}

İsim: {name}

Profil:
- Sosyallik: {profile["social"]}
- Karar tarzı: {profile["decision"]}
- Motivasyon: {profile["motivation"]}
- Çalışma tarzı: {profile["work_style"]}
- Rol: {profile["role"]}

Cevaplar:
- q1: {answer_texts.get("q1", "")}
- q2: {answer_texts.get("q2", "")}
- q3: {answer_texts.get("q3", "")}
- q4: {answer_texts.get("q4", "")}
- q5: {answer_texts.get("q5", "")}
- q6: {answer_texts.get("q6", "")}
- q7: {answer_texts.get("q7", "")}
- q8: {answer_texts.get("q8", "")}
""".strip()

    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
    }

    response = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
    data = response.json()

    try:
        text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise Exception(data)

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    parsed = json.loads(text)

    return {
        "short_summary": str(parsed["short_summary"]).strip(),
        "five_year_story": str(parsed["five_year_story"]).strip(),
    }


def sanitize_text(text: str, fallback: str) -> str:
    clean = str(text).strip()
    if not clean:
        return fallback
    return clean


def build_fallback_summary(name: str, profile: Dict[str, str]) -> str:
    return (
        f"{name}, {profile['decision'].lower()} düşünme biçimi ve "
        f"{profile['motivation'].lower()} yaklaşımıyla dikkat çekiyor. "
        f"{profile['work_style'].lower()} çalışma tarzı ve {profile['role'].lower()} yönü, "
        f"onu belirli hedeflere odaklanabilen biri haline getiriyor."
    )


def build_fallback_story(name: str, profile: Dict[str, str], career_suggestions: List[str]) -> str:
    return (
        f"Önümüzdeki yıllarda {name}, {career_suggestions[0].lower()} alanında daha görünür hale gelebilir. "
        f"{profile['decision'].lower()} yaklaşımı ve {profile['motivation'].lower()} yapısı, "
        f"zamanla daha güçlü kararlar almasına yardımcı olabilir. "
        f"Bu süreç, onu hem iş üreten hem de çevresine güven veren biri haline getirebilir."
    )

# =========================================================
# PDF YARDIMCILARI
# =========================================================
def draw_round_box(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    fill_color,
    stroke_color=None,
    radius: int = 16,
    stroke_width: int = 1,
):
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(stroke_width)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    else:
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)


def draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float = 15,
    font_name: str = FONT_NAME,
    font_size: int = 10,
    color=black,
):
    c.setFillColor(color)
    c.setFont(font_name, font_size)

    words = str(text).split()
    line = ""
    current_y = y

    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            c.drawString(x, current_y, line)
            current_y -= line_height
            line = word

    if line:
        c.drawString(x, current_y, line)
        current_y -= line_height

    return current_y


def draw_section_heading(
    c: canvas.Canvas,
    title: str,
    x: float,
    y: float,
    width: float,
    font_name: str = FONT_NAME,
):
    bar_height = 24
    bar_y = y - bar_height + 4

    c.setFillColor(HexColor("#E0E7FF"))
    c.roundRect(x, bar_y, width, bar_height, 10, fill=1, stroke=0)

    c.setFillColor(HexColor("#312E81"))
    c.setFont(font_name, 11)
    c.drawString(x + 12, bar_y + 7, title)


def draw_chip_row(
    c: canvas.Canvas,
    items: List[str],
    x: float,
    y: float,
    max_width: float,
    font_name: str = FONT_NAME,
):
    chip_height = 20
    gap = 8
    cursor_x = x
    cursor_y = y

    for item in items:
        text = str(item)
        chip_width = max(62, c.stringWidth(text, font_name, 9) + 20)

        if cursor_x + chip_width > x + max_width:
            cursor_x = x
            cursor_y -= (chip_height + 8)

        c.setFillColor(HexColor("#EEF2FF"))
        c.setStrokeColor(HexColor("#C7D2FE"))
        c.roundRect(cursor_x, cursor_y - chip_height, chip_width, chip_height, 10, fill=1, stroke=1)

        c.setFillColor(HexColor("#3730A3"))
        c.setFont(font_name, 9)
        c.drawString(cursor_x + 10, cursor_y - 13, text)

        cursor_x += chip_width + gap

    return cursor_y - 26


def draw_single_chip(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = FONT_NAME,
):
    chip_height = 24
    text_width = c.stringWidth(text, font_name, 10) + 24
    chip_width = min(max_width, max(100, text_width))

    c.setFillColor(HexColor("#EEF2FF"))
    c.setStrokeColor(HexColor("#C7D2FE"))
    c.roundRect(x, y - chip_height, chip_width, chip_height, 10, fill=1, stroke=1)

    c.setFillColor(HexColor("#3730A3"))
    c.setFont(font_name, 10)
    c.drawString(x + 12, y - 16, text)

    return y - 30

# =========================================================
# PDF RAPOR
# =========================================================
def create_pdf_report(
    session_id: str,
    name: str,
    profile: Dict[str, str],
    result_payload: Dict[str, object],
    report_url: str,
) -> Path:
    pdf_path = PDF_DIR / f"{session_id}.pdf"
    qr_img_path = QR_DIR / f"{session_id}_embedded.png"

    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(report_url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(qr_img_path)

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    margin = 36
    content_width = width - (2 * margin)

    c.setFillColor(HexColor("#F8FAFC"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    c.setFillColor(HexColor("#0F172A"))
    c.rect(0, height - 150, width, 150, fill=1, stroke=0)

    if LOGO_PATH.exists():
        logo_size = 78
        logo_x = width - 120
        logo_y = height - 95

        try:
            c.drawImage(
                str(LOGO_PATH),
                logo_x,
                logo_y,
                width=logo_size,
                height=logo_size,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    c.setFillColor(white)
    c.setFont(FONT_NAME, 24)
    c.drawString(margin, height - 56, "AI Knows You")

    c.setFont(FONT_NAME, 15)
    c.drawString(margin, height - 82, f"{name} için Kişisel Analiz Raporu")

    c.setFillColor(HexColor("#CBD5E1"))
    c.setFont(FONT_NAME, 9)
    c.drawString(
        margin,
        height - 106,
        f"Oluşturulma zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    y = height - 175

    draw_round_box(
        c,
        margin,
        y - 64,
        content_width,
        58,
        HexColor("#FFFFFF"),
        HexColor("#E2E8F0"),
        radius=16,
    )

    c.setFillColor(HexColor("#0F172A"))
    c.setFont(FONT_NAME, 11)

    summary_line_1 = f"Sosyallik: {profile['social']}, Karar tarzı: {profile['decision']}, Rol: {profile['role']}"
    summary_line_2 = f"Motivasyon: {profile['motivation']}, Çalışma tarzı: {profile['work_style']}"

    c.drawString(margin + 16, y - 22, summary_line_1)
    c.drawString(margin + 16, y - 42, summary_line_2)

    y -= 82

    draw_section_heading(c, "Kısa içgörü", margin, y, content_width, FONT_NAME)
    y -= 32

    summary_box_height = 76
    draw_round_box(
        c,
        margin,
        y - summary_box_height + 10,
        content_width,
        summary_box_height,
        HexColor("#FFFFFF"),
        HexColor("#E2E8F0"),
        radius=16,
    )

    draw_wrapped_text(
        c,
        result_payload["short_summary"],
        margin + 16,
        y - 14,
        content_width - 32,
        line_height=15,
        font_name=FONT_NAME,
        font_size=10,
        color=HexColor("#334155"),
    )

    y -= summary_box_height + 6

    card_gap = 16
    card_width = (content_width - card_gap) / 2
    card_height = 82

    left_x = margin
    right_x = margin + card_width + card_gap
    card_y = y - card_height

    draw_round_box(
        c,
        left_x,
        card_y,
        card_width,
        card_height,
        HexColor("#ECFDF5"),
        HexColor("#A7F3D0"),
        radius=16,
    )
    c.setFillColor(HexColor("#065F46"))
    c.setFont(FONT_NAME, 11)
    c.drawString(left_x + 14, card_y + card_height - 18, "Süper gücün")
    draw_wrapped_text(
        c,
        result_payload["super_power"],
        left_x + 14,
        card_y + card_height - 36,
        card_width - 28,
        line_height=13,
        font_name=FONT_NAME,
        font_size=9,
        color=HexColor("#065F46"),
    )

    draw_round_box(
        c,
        right_x,
        card_y,
        card_width,
        card_height,
        HexColor("#FFF1F2"),
        HexColor("#FECDD3"),
        radius=16,
    )
    c.setFillColor(HexColor("#9F1239"))
    c.setFont(FONT_NAME, 11)
    c.drawString(right_x + 14, card_y + card_height - 18, "Seni zorlayabilecek nokta")
    draw_wrapped_text(
        c,
        result_payload["blocking_point"],
        right_x + 14,
        card_y + card_height - 36,
        card_width - 28,
        line_height=13,
        font_name=FONT_NAME,
        font_size=9,
        color=HexColor("#9F1239"),
    )

    y = card_y - 14

    draw_section_heading(c, "Sana uygun alanlar", margin, y, content_width, FONT_NAME)
    y -= 28
    y = draw_chip_row(c, result_payload["career_suggestions"], margin, y, content_width, FONT_NAME)

    draw_section_heading(c, "Önerilen meslek", margin, y, content_width, FONT_NAME)
    y -= 28
    y = draw_single_chip(c, result_payload["job_suggestion"], margin, y, content_width, FONT_NAME)

    draw_section_heading(c, "5 yıl sonra sen", margin, y, content_width, FONT_NAME)
    y -= 32

    story_box_height = 92
    draw_round_box(
        c,
        margin,
        y - story_box_height + 10,
        content_width,
        story_box_height,
        HexColor("#FFFFFF"),
        HexColor("#E2E8F0"),
        radius=16,
    )

    draw_wrapped_text(
        c,
        result_payload["five_year_story"],
        margin + 16,
        y - 14,
        content_width - 32,
        line_height=15,
        font_name=FONT_NAME,
        font_size=10,
        color=HexColor("#334155"),
    )

    footer_y = 44
    footer_height = 76

    draw_round_box(
        c,
        margin,
        footer_y,
        content_width,
        footer_height,
        HexColor("#EFF6FF"),
        HexColor("#BFDBFE"),
        radius=16,
    )

    c.setFillColor(HexColor("#1E3A8A"))
    c.setFont(FONT_NAME, 10)
    c.drawString(margin + 16, footer_y + 46, "Ankara Üniversitesi Bilişim Teknolojileri Meslek Yüksekokulu tarafından tasarlanan bu deneyimin bir")

    c.setFillColor(HexColor("#1E3A8A"))
    c.setFont(FONT_NAME, 10)
    c.drawString(margin + 16, footer_y + 30, "parçası olduğunuz için teşekkür ederiz.")

    c.setFillColor(HexColor("#475569"))
    c.setFont(FONT_NAME, 7)
    c.drawString(margin + 16, footer_y + 10, report_url[:95])

    try:
        c.drawImage(
            str(qr_img_path),
            width - 98,
            footer_y + 14,
            width=46,
            height=46,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        pass

    c.save()
    return pdf_path


def create_qr_for_pdf(session_id: str, pdf_url: str) -> Path:
    qr_path = QR_DIR / f"{session_id}.png"
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(pdf_url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(qr_path)
    return qr_path

# =========================================================
# ROUTES
# =========================================================
@app.get("/")
def root():
    return {"message": "AI Knows You yerel backend çalışıyor."}


@app.get("/questions")
def get_questions():
    return {"questions": QUESTIONS}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    if len(payload.answers) != 8:
        raise HTTPException(status_code=400, detail="Tam olarak 8 cevap gönderilmelidir.")

    seen = set()
    for item in payload.answers:
        if item.question_id in seen:
            raise HTTPException(status_code=400, detail=f"Aynı soru iki kez gönderildi: {item.question_id}")
        seen.add(item.question_id)

    expected_ids = {f"q{i}" for i in range(1, 9)}
    if seen != expected_ids:
        raise HTTPException(status_code=400, detail="q1 ile q8 arasındaki tüm sorular cevaplanmalıdır.")

    name = (payload.name or "Katılımcı").strip()
    session_id = uuid.uuid4().hex[:8]

    raw_scores = score_answers(payload.answers)
    profile = build_profile(raw_scores)
    answer_texts = answers_to_text_map(payload.answers)

    super_power = build_super_power(profile)
    blocking_point = build_blocking_point(profile)
    career_suggestions = build_career_suggestions(profile)
    job_suggestion = build_best_job_suggestion(profile)

    fallback_summary = build_fallback_summary(name, profile)
    fallback_story = build_fallback_story(name, profile, career_suggestions)

    try:
        ai_generated = call_local_ai_summary_and_story(name, profile, answer_texts)
        short_summary = sanitize_text(ai_generated["short_summary"], fallback_summary)
        five_year_story = sanitize_text(ai_generated["five_year_story"], fallback_story)
    except Exception:
        short_summary = fallback_summary
        five_year_story = fallback_story

    result_payload = {
        "short_summary": short_summary,
        "super_power": super_power,
        "blocking_point": blocking_point,
        "career_suggestions": career_suggestions,
        "job_suggestion": job_suggestion,
        "five_year_story": five_year_story,
    }

    pdf_path = create_pdf_report(
        session_id,
        name,
        profile,
        result_payload,
        f"{BASE_URL}/generated/pdfs/{session_id}.pdf",
    )
    pdf_url = f"{BASE_URL}/generated/pdfs/{pdf_path.name}"

    qr_path = create_qr_for_pdf(session_id, pdf_url)
    qr_url = f"{BASE_URL}/generated/qrs/{qr_path.name}"

    return {
        "session_id": session_id,
        "profile": profile,
        "raw_scores": raw_scores,
        "answer_texts": answer_texts,
        "ai_result": result_payload,
        "pdf_url": pdf_url,
        "qr_url": qr_url,
        "report_url": pdf_url,
    }