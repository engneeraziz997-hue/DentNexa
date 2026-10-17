# DentNexa 🦷🤖

مساعد افتراضي مؤسسي لعيادات الأسنان يعمل بالذكاء الاصطناعي التفاعلي عبر منصة **WhatsApp**، مدمج بتقنيات **LangGraph**, **FastMCP**, **Pinecone Vector DB**, و **PostgreSQL**.

مشروع **DentNexa** هو وكيل ذكاء اصطناعي مؤسسي مفتوح المصدر يعمل كمساعد عيادة افتراضي محترف باسم **"سيا"**. يقوم بأتمتة التواصل مع المرضى عبر واتساب باللغة العربية، الاستعلام من قاعدة البيانات المتجهة **Pinecone RAG** بخصوص الأسعار والنصائح الطبية والتأمين، حجز وتعديل وإلغاء المواعيد، تسجيل المرضى الجدد، تحويل المحادثات لموظف الاستقبال البشري، وإرسال تذكيرات تلقائية للمواعيد على مدار 24 ساعة طوال الأسبوع.

---

## ✨ المميزات الرئيسية للمشروع المؤسسي

- **واجهة تفاعلية عبر واتساب (WhatsApp Business API)**: التواصل الفوري المباشر مع المرضى باللغة العربية الفصحى الودودة.
- **نظام RAG المتجهي عبر Pinecone Vector DB 🌲**: بحث واسترجاع ذكي للمعلومات الطبية، قائمة الأسعار، الخدمات، وسياسات التأمين باستخدام متجهات `text-embedding-3-small`.
- **تحويل المحادثة لموظف الاستقبال البشري (Human Escalation) 👤**: أداة `escalate_to_human` لشفافية التحويل عند طلب المريض أو الحالات المعقدة.
- **إدارة المواعيد الأوتوماتيكية**: حجز المواعيد الجديدة، تعديل المواعيد القائمة، أو إلغاؤها مع التحقق من التعارض الزمني.
- **تذكيرات المواعيد التلقائية ⏰**: فحص وإرسال تذكيرات تلقائية للمرضى عبر واتساب قبل موعدهم بـ 24 ساعة.
- **دعم قواعد البيانات PostgreSQL & SQLite 🐘**: طبقة بيانات مرنة تدعم PostgreSQL للبيئات الإنتاجية الضخمة بجانب SQLite.
- **ذاكرة استمرارية (Persistent Sessions)**: حفظ واسترجاع كامل سياق الجلسات والرسائل السابقة.

---

## ⚙️ آلية عمل البنية التحتية

تم تصميم **DentNexa** وفق معمارية منفصلة الكيانات (Decoupled Architecture) لضمان الاستقرار والسرعة:

1. **الوكيل الرئيسي (`src/app`)**: إدارة الرسم البياني `StateGraph` عبر LangGraph، ذاكرة الجلسات، والمهام الخفية في الخلفية (`appointment_reminder_task` و `conversation_cleanup_task`).
2. **خادم الأدوات (`src/dentnexa_mcp`)**: يوفر خادم FastMCP أدوات العيادة:
   - `search_knowledge_base`: الاستعلام من Pinecone RAG وقاعدة المعرفة.
   - `escalate_to_human`: تحويل المحادثة لموظف الاستقبال البشري.
   - `send_appointment_reminders`: إطلاق التذكيرات التلقائية للمواعيد.
   - `book_appointment`, `cancel_appointment`, `reschedule_appointment`.
   - `update_patient_profile` و `get_current_time`.
3. **طبقة البيانات والمحركات (`src/shared`)**:
   - `rag.py`: محرك RAG المربوط بـ Pinecone و OpenAI Embeddings.
   - `ingest_kb.py`: سكريبت رفع وفهرسة البيانات إلى Pinecone Index.
   - `db.py`: محول قواعد البيانات PostgreSQL / SQLite.

---

## 🚀 البدء والتشغيل

### 1. الإعداد وتثبيت التبعيات

```sh
# 1. نسخ المستودع والدخول للمجلد
git clone git@github.com:oxi-p/DentNexa.git
cd DentNexa

# 2. تثبيت الحزم وتنسيق البيئة
uv sync

# 3. إعداد ملف البيئة
cp example.env .env
```

### 2. تهيئة ملف المتغيرات البيئية (`.env`)

قم بضبط المفاتيح التالية في ملف `.env`:
- `OPENAI_API_KEY`: مفتاح OpenAI للنموذج والتطمين المتجهي.
- `PINECONE_API_KEY` و `PINECONE_INDEX_NAME`: مفتاح وفهرس Pinecone Vector DB.
- `DATABASE_URL` أو `POSTGRES_HOST`: تصاريح الاتصال بقاعدة بيانات PostgreSQL.
- `META_ACCESS_TOKEN` و `META_PHONE_NUMBER_ID`: بيانات Meta WhatsApp API.

### 3. رفع قاعدة المعرفة لـ Pinecone (Knowledge Ingestion)

لتغدية قاعدة بيانات Pinecone بالأسعار والخدمات والنصائح الطبية:
```sh
uv run src/shared/ingest_kb.py
```

### 4. تشغيل التطبيق والخدمات

تشغيل سيرفر الـ Webhook الخفي وخادم MCP:
```sh
uv run server
```

---

## 🛠️ هيكل المجلدات والملفات

```text
DentNexa/
├── data/
│   ├── knowledge_base/
│   │   └── clinic_faq.json   # قاعدة المعرفة (الأسعار، التأمين، النصائح)
│   └── dentnexa_app.db       # قاعدة بيانات SQLite المحليات
├── src/
│   ├── app/                  # محرك المحادثة وواتساب والمهام الخفية
│   │   ├── agent.py          # رسم LangGraph والمهام الخلفية التلقائية
│   │   ├── main.py           # سيرفر FastAPI والتحقق الرقمي HMAC
│   │   ├── whatsapp.py       # صياغة وإرسال رسائل واتساب المنسقة
│   │   └── mcp_client.py     # عميل اختبار الأدوات
│   ├── dentnexa_mcp/         # خادم FastMCP والأدوات المتاحة
│   │   └── server.py
│   └── shared/               # قواعد البيانات وRAG والنماذج
│       ├── db.py             # محول قواعد البيانات PostgreSQL / SQLite
│       ├── rag.py            # محرك البحث المتجهي في Pinecone
│       ├── ingest_kb.py      # سكريبت رفع الفهارس لـ Pinecone
│       └── models.py         # هياكل Pydantic
├── .env                      # متغيرات البيئة الفعالة
├── example.env               # نموذج ملف البيئة الشامل
├── pyproject.toml            # إعدادات وتسمية الحزمة
└── README.md                 # دليل التوثيق الحالي باللغة العربية
```

---

## 📄 الترخيص

هذا المشروع مرخص بموجب رخصة MIT License.
