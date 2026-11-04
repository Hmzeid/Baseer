/* Baseer console — single-page app over the FastAPI surface.
   Hash routes: #/overview #/inspect #/live #/inspections #/report/<id>?f=<n>
   #/cases?status=<s> #/audit #/users #/account. No build step, no framework. */
"use strict";

/* ------------------------------------------------------------------ icons */
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
  "plus-square": '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 8v8M8 12h8"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  camera: '<path d="M15 10l5-3v10l-5-3z"/><rect x="3" y="6" width="12" height="12" rx="2.5"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  clipboard: '<rect x="8" y="3" width="8" height="4" rx="1"/><path d="M16 5h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2"/><path d="M9 14l2 2 4-4"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  user: '<circle cx="12" cy="8" r="4.5"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  download: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
  printer: '<path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="7" rx="1"/>',
  share: '<path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M16 6l-4-4-4 4M12 2v13"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
  send: '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M20 16v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  alert: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  chevron: '<path d="M9 18l6-6-6-6"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="8.5" cy="9.5" r="1.5"/><path d="M21 15l-5-5L5 20"/>',
  video: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M10 9l5 3-5 3z"/>',
  sparkles: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3v4M21 5h-4"/>',
  key: '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3L21 2M17 6l3 3M15 8l2 2"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
  message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  filter: '<path d="M3 4h18l-7 8.5V19l-4 2v-8.5z"/>',
  play: '<path d="M7 4l13 8-13 8z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  "check-shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  wrench: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  scan: '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1.5"/>',
  volume: '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;
}
function paintIcons(root = document) {
  root.querySelectorAll("i[data-icon]").forEach((el) => {
    if (el.dataset.painted === el.dataset.icon) return;
    el.innerHTML = icon(el.dataset.icon);
    el.dataset.painted = el.dataset.icon;
  });
}
const ic = (name, cls = "") => `<i data-icon="${name}" class="${cls}" data-painted="${name}">${icon(name)}</i>`;

/* ------------------------------------------------------------------- i18n */
const S = {
  ar: {
    dir: "rtl",
    brandSub: "منصة الفحص الميداني", madeBy: "منتج من",
    loginHero: "الفحص الميداني الذي يرى ويفهم ويتصرف — بالعربية.",
    loginHeroSub: "حوّل جولة الموقع إلى تقرير سلامة موثّق بالأدلة، وتابع كل إجراء تصحيحي حتى يعتمد إنسانٌ إغلاقه.",
    loginP1: "تقرير منظم في نحو 30 ثانية من صور أو فيديو",
    loginP2: "كاميرا مباشرة ترصد المخالفات لحظة ظهورها",
    loginP3: "إغلاق الحالات باعتماد بشري وسجل تدقيق لا يُحذف",
    loginT: "تسجيل الدخول", loginHint: "حسابك الشخصي — كل إجراء يُسجَّل باسمك.",
    loginUser: "اسم المستخدم", loginPass: "كلمة المرور", loginGo: "دخول", showPw: "إظهار كلمة المرور",
    loginErr: "تعذّر الدخول — تحقق من الاسم وكلمة المرور.", loginThrottled: "محاولات كثيرة — انتظر 5 دقائق.",
    theme: "تبديل المظهر", logout: "خروج",
    navOps: "العمليات", navOverview: "نظرة عامة", navInspect: "فحص جديد", navLive: "كاميرا مباشرة",
    navRecords: "السجلات", navInspections: "الفحوصات", navCases: "الحالات", navAudit: "سجل التدقيق",
    navAdmin: "الحساب", navUsers: "المستخدمون", navAccount: "حسابي",
    searchPh: "ابحث في الفحوصات أو أدخل رقم فحص…",
    crumb: "بصير",
    pT: { overview: "نظرة السلامة العامة", inspect: "فحص جديد", live: "الكاميرا المباشرة", inspections: "سجل الفحوصات",
      report: "تقرير الفحص", cases: "الإجراءات التصحيحية", audit: "سجل التدقيق", users: "المستخدمون", account: "حسابي" },
    pS: { overview: "مؤشرات السلامة عبر المواقع: الملاحظات، والخطورة، والحالات المفتوحة والمتأخرة.",
      inspect: "صور أو فيديو مع ملاحظة المفتش — والنتيجة تقرير كامل في نحو 30 ثانية.",
      live: "إطارات تصل تباعًا، ومخالفات تُرصد لحظة ظهورها، وتقرير كامل عند إنهاء الجلسة.",
      inspections: "كل الفحوصات المكتملة — ابحث وصفِّ وافتح أي تقرير.",
      report: "تقرير مبني على الأدلة — كل ملاحظة مرتبطة بإطارها، ولا تُغلق إلا باعتماد بشري.",
      cases: "كل حالة إجراء تصحيحي عبر الفحوصات، مرتبة حسب الأولوية والموعد النهائي.",
      audit: "كل إجراء على الحالات — إسنادًا وتحققًا واعتمادًا وملاحظات — مسجل ولا يُحذف.",
      users: "حسابات المفتشين وأدوارهم — للإدارة فقط.", account: "ملفك الشخصي وتفضيلاتك وكلمة المرور." },
    ctaNew: "فحص جديد", siteFilter: "الموقع", siteAll: "كل المواقع",
    seedNote: "تتضمن هذه الأرقام بيانات تجريبية للعرض، وتُستبدل تلقائيًا مع تراكم الفحوصات الحقيقية.",
    aTotal: "الفحوصات", dTotal: "فحوصات مسجلة", aFindings: "الملاحظات", dFindings: (n) => `${n} لكل فحص في المتوسط`,
    aHigh: "عالية الخطورة", dHigh: "تتطلب تدخلًا فوريًا", aOpen: "حالات مفتوحة", dOpen: (r) => `نسبة الإغلاق ${r}%`,
    aOverdue: "متأخرة", dOverdue: "تجاوزت الموعد النهائي",
    trendT: "النشاط اليومي", trendN: (n) => `${n} فحصًا خلال 14 يومًا`, legInsp: "الفحوصات", legFind: "الملاحظات",
    sevMix: "توزيع الخطورة", sevTotal: (n) => `${n} ملاحظة`, topHazards: "أكثر المخاطر تكرارًا",
    agingT: "حالات تحتاج متابعة", viewAll: "عرض الكل", recent: "أحدث الفحوصات",
    pipeT: "من الجولة الميدانية إلى الإغلاق الموثّق", pipeHint: "كل فحص يمر بالحلقة نفسها — والملاحظة لا تُغلق أبدًا إلا باعتماد بشري.",
    loop: [["رصد", "صور أو فيديو أو بث مباشر"], ["فهم", "تجزئة المشهد بنماذج Meta"], ["شرح", "تقرير عربي بالأدلة"],
      ["إجراء", "حالة لكل ملاحظة"], ["تحقق", "إعادة فحص بدليل جديد"], ["إغلاق", "باعتماد بشري فقط"]],
    noData: "لا بيانات بعد.", demo: "تجريبي", times: (n) => `${n} مرة`,
    newInspect: "فحص جديد", newHint: "تقرير كامل في نحو 30 ثانية",
    dropTitle: "اسحب الصور أو الفيديو هنا أو اضغط للاختيار", dropSub: "JPG · PNG · WEBP · MP4 · MOV — حتى 150 ميغابايت",
    notes: "ملاحظات المفتش (صوتية مفرّغة أو مكتوبة)", notesPh: "مثال: لاحظت عاملًا عند الحافة العلوية، والرافعة تعمل قرب منطقة المشاة…",
    micRec: "تسجيل ملاحظة صوتية", micStop: "إيقاف التسجيل", micListening: "يستمع… تحدث الآن.",
    micDone: "أُضيفت النسخة إلى الملاحظات.", micErr: "النسخ الصوتي غير متاح — اكتب الملاحظة بدلًا من ذلك.",
    ctx: "الموقع / سياق الفحص", ctxPh: "مثال: factory — فحص سلامة أسبوعي",
    run: "إنشاء التقرير", clear: "مسح", running: "يحلل بصير الموقع…",
    progress: ["رفع الأدلة", "استخراج الإطارات", "تحليل المشهد", "كتابة التقرير"],
    needInput: "أضف صورة أو فيديو أو ملاحظة مكتوبة أولًا.", done: "تم إنشاء التقرير.", error: "تعذّر إنشاء التقرير.",
    guideT: "ماذا يفحص بصير؟",
    guide: ["معدات الوقاية الشخصية: خوذة، سترة عاكسة، قفازات، نظارات.", "مخاطر الحركة: مسارات الرافعات، الحواف العلوية، الحواجز.",
      "مخاطر الماكينات: الواقيات، مخارج الطوارئ، العلامات الأرضية."],
    guideNote: "التقرير يستند إلى ما يظهر في الإطار فقط — وما لا يمكن تحديده يُسجَّل كذلك، ولا يُرفع مستوى الخطورة عند الشك.",
    howT: "كيف يعمل الفحص؟",
    how: [["الدليل", "ارفع صورًا أو فيديو قصيرًا وأضف ملاحظتك."], ["الفهم", "تُجزّأ المشاهد ويُستدل على المخاطر مع ملاحظتك."],
      ["التقرير", "ملاحظات بخطورتها وإطارها وإجرائها التصحيحي."], ["المتابعة", "كل ملاحظة تفتح حالة تُتابَع حتى الإغلاق."]],
    stageIdle: "الكاميرا متوقفة — ابدأ جلسة ثم شغّل الكاميرا أو أرسل إطارًا من ملف.",
    kLiveState: "الحالة", liveFrames: "إطارات مستلمة", liveAlertsT: "تنبيهات", liveOn: "مباشرة", liveIdle: "خاملة",
    liveStart: "بدء جلسة مباشرة", liveCamT: "تشغيل الكاميرا", camStop: "إيقاف الكاميرا", liveSendFile: "إرسال إطار من ملف",
    liveFinish: "إنهاء الجلسة وإنتاج التقرير", resumeHint: "جلسات غير مكتملة:", resume: "استئناف",
    liveCtx: "الموقع", liveHint: "تحليل شبه لحظي — لقطة كل 3 ثوانٍ، والتنبيه يظهر عند أول رصد لكل مخالفة.",
    liveStarted: "بدأت الجلسة المباشرة.", camDenied: "تعذّر الوصول إلى الكاميرا — أرسل إطارًا من ملف بدلًا من ذلك.",
    camOn: "الكاميرا تعمل — لقطة كل 3 ثوانٍ.", frames: (n) => `${n} إطار`,
    alertsT: "التنبيهات المباشرة", alertsN: (n) => `${n} تنبيه`, noAlerts: "لا تنبيهات بعد — ستظهر هنا لحظة رصد مخالفة.",
    frameN: (i) => `الإطار ${i + 1}`, finishing: "يُنتج التقرير…",
    histSearchPh: "ابحث برقم الفحص أو الموقع أو نوع الخطر…", csvBtn: "تصدير CSV", sevAll: "كل الخطورات",
    colId: "رقم الفحص", colDate: "التاريخ", thSite: "الموقع", colSource: "المصدر", colFindings: "الملاحظات", colCases: "الحالات",
    histEmpty: "لا توجد فحوصات مطابقة.", srcUpload: "رفع ملفات", srcLive: "كاميرا مباشرة",
    closedOf: (c, t) => `${c}/${t} مغلقة`,
    noReport: "لم يُفتح تقرير بعد", noReportHint: "شغّل فحصًا جديدًا، أو افتح تقريرًا من سجل الفحوصات.",
    report: "تقرير", pdfRep: "PDF", printRep: "طباعة", shareWa: "واتساب", copyLink: "نسخ الرابط", linkCopied: "نُسخ رابط التقرير.",
    tEvidence: "الأدلة المرفقة", findings: "الملاحظات", findingsN: (n) => `${n} ملاحظات`, noFindings: "لا ملاحظات — لم يُرصد ما يستدعي إجراءً.",
    meta: (r) => `${fmtTime(r.created_at)} · ${r.frames_processed} إطار · الموقع: ${siteName(r)}`,
    stripTotal: "الملاحظات", noEvidence: "لا ملفات مرفقة — تقرير مبني على ملاحظة المفتش.",
    more: (n) => `+${n} أخرى`, loadVideo: "تشغيل الفيديو",
    action: "الإجراء التصحيحي", frame: (i) => `الإطار ${i + 1}`,
    srcSeg: "النموذج البصري", srcInsp: "ملاحظة المفتش", srcBoth: "النموذج + المفتش", detUncertain: "تعذّر التحديد",
    sev: { high: "عالية", medium: "متوسطة", low: "منخفضة" },
    pipeBadgeMock: "بيانات تجريبية", pipeBadgeVision: "رؤية Muse", pipeBadgeSam: "SAM 3.1",
    caseT: "الإجراء التصحيحي", due: (d) => `الموعد: ${d}`, overdue: "متأخرة",
    steps: ["مفتوحة", "مُسندة", "تم التحقق", "مغلقة"],
    status: { open: "مفتوحة", assigned: "مُسندة", closed: "مغلقة", overdue: "متأخرة" },
    assignPh: "إسناد إلى…", assign: "إسناد", verify: "تحقق ذكي", verPhoto: "دليل إعادة الفحص", approve: "اعتماد الإغلاق",
    roles: ["مشرف السلامة", "مدير الموقع", "المقاول"],
    approveQ: "اعتماد إغلاق هذه الحالة؟", approveBody: "سيُسجَّل الإغلاق باسمك في سجل التدقيق ولا يمكن التراجع عنه.",
    activity: (n) => `النشاط (${n})`, notePh: "أضف ملاحظة إلى سجل الحالة…", noteAdd: "إضافة",
    act: { assign: "إسناد", verify: "تحقق", approve: "اعتماد الإغلاق", verify_evidence: "تحقق بدليل", note: "ملاحظة" },
    assigned: "أُسندت الحالة.", verified: "اكتمل التحقق.", closed: "أُغلقت الحالة.", noteSaved: "أُضيفت الملاحظة.",
    briefT: "إحاطة الطاقم", briefHint: "حديث سلامة قصير من هذا التقرير، بلغة الطاقم، للقراءة بصوت عالٍ",
    briefPick: "اختر لغة الطاقم لإنشاء الإحاطة.", briefCopy: "نسخ", briefRead: "قراءة بصوت", briefRedo: "إعادة الإنشاء",
    briefCopied: "نُسخت الإحاطة.", briefNoVoice: (n) => `لا يتوفر صوت ${n} على هذا الجهاز.`, briefWorking: "يكتب بصير الإحاطة…",
    segToggle: (src, n, on) => `مقاطع SAM 3.1 (${n}) · ${on ? "إخفاء" : "إظهار"}`,
    chat: "اسأل بصير", chatHint: "إجابات مستندة إلى أدلة هذا الفحص فقط.", chatPh: "اسأل عن أي ملاحظة أو اطلب مسودة إشعار…",
    send: "إرسال", chatErr: "تعذّرت الإجابة الآن.",
    chips: (f) => [f ? `لماذا «${f.title_ar || f.title_en}» ${S.ar.sev[f.severity] || ""} الخطورة؟` : "ما أخطر ملاحظة؟",
      "صِغ إشعارًا للمقاول", "لخّص التقرير لمدير الموقع"],
    tabs: { all: "الكل", open: "مفتوحة", assigned: "مُسندة", overdue: "متأخرة", closed: "مغلقة" },
    colCase: "الحالة", colCaseSev: "الخطورة", colStatus: "الوضع", colAssignee: "المسؤول", colDue: "الموعد النهائي",
    casesEmpty: "لا حالات هنا — كل شيء تحت السيطرة.", unassigned: "غير مُسندة",
    dueIn: (d) => d <= 0 ? "اليوم" : `خلال ${d} يوم`, dueAgo: (d) => `متأخرة ${d} يوم`,
    auditSearchPh: "ابحث في السجل…", actAll: "كل الإجراءات",
    thTime: "الوقت", thAuditId: "الفحص", thFindingN: "ملاحظة #", thAction: "الإجراء", thActor: "الفاعل", thDetail: "التفاصيل",
    auditEmpty: "لا إجراءات مسجلة بعد.",
    tUsers: "المستخدمون", usersN: (n) => `${n} حساب`, thUName: "المستخدم", thURole: "الدور", thUCreated: "أُنشئ",
    tNewUser: "حساب جديد", tNuName: "اسم المستخدم", tNuPass: "كلمة المرور (8 أحرف على الأقل)", tNuRole: "الدور", nuAdd: "إضافة المستخدم",
    userAdded: "أُضيف المستخدم.", roleSaved: "حُدّث الدور.", resetPw: "إعادة تعيين كلمة المرور",
    resetQ: (u) => `كلمة مرور جديدة لـ ${u}`, resetBody: "8 أحرف على الأقل. أبلغ المستخدم بها عبر قناة آمنة.", pwReset: "أُعيد تعيين كلمة المرور.",
    delUser: "حذف", delQ: (u) => `حذف المستخدم ${u}؟`, delBody: "لن يتمكن من الدخول بعد الآن. يبقى سجل التدقيق كما هو.", userDeleted: "حُذف المستخدم.",
    you: "أنت",
    prefLang: "اللغة", prefLangHint: "لغة الواجهة والتقارير المعروضة.", prefTheme: "المظهر", prefThemeHint: "فاتح أو داكن.",
    light: "فاتح", dark: "داكن",
    tMyPass: "تغيير كلمة المرور", tPwOld: "كلمة المرور الحالية", tPwNew: "كلمة المرور الجديدة (8+)", pwChange: "تحديث كلمة المرور",
    pwOk: "تم تغيير كلمة المرور.", pwErr: "تعذّر التغيير — تحقق من كلمة المرور الحالية.",
    about: (h) => `بصير ${h.version || ""} من Veebase · الوضع: ${h.mode === "live" ? "مباشر" : "تجريبي"} · © ${new Date().getFullYear()} Veebase`,
    modeLive: "مباشر", modeMock: "تجريبي", modeLiveS: "نماذج Meta متصلة", modeMockS: "مخرجات تجريبية، دون مفاتيح API",
    ok: "موافق", cancel: "إلغاء", confirm: "تأكيد", notFound: "التقرير غير موجود.", genericErr: "حدث خطأ.",
    seedRow: "سجل تجريبي للعرض — لا يحتوي تقريرًا كاملًا.",
  },
  en: {
    dir: "ltr",
    brandSub: "Field inspection console", madeBy: "A product by",
    loginHero: "Field inspection that sees, understands and acts — in Arabic.",
    loginHeroSub: "Turn a site walkthrough into an evidence-grounded safety report, then track every corrective action until a human approves the closure.",
    loginP1: "A structured report in about 30 seconds from photos or video",
    loginP2: "A live camera that flags violations the moment they appear",
    loginP3: "Human-approved closures and an append-only audit trail",
    loginT: "Sign in", loginHint: "Your personal account — every action is recorded under your name.",
    loginUser: "Username", loginPass: "Password", loginGo: "Sign in", showPw: "Show password",
    loginErr: "Sign-in failed — check your username and password.", loginThrottled: "Too many attempts — wait 5 minutes.",
    theme: "Toggle theme", logout: "Sign out",
    navOps: "Operations", navOverview: "Overview", navInspect: "New inspection", navLive: "Live camera",
    navRecords: "Records", navInspections: "Inspections", navCases: "Cases", navAudit: "Audit log",
    navAdmin: "Account", navUsers: "Users", navAccount: "My account",
    searchPh: "Search inspections or paste an inspection ID…",
    crumb: "Baseer",
    pT: { overview: "Safety overview", inspect: "New inspection", live: "Live camera", inspections: "Inspection history",
      report: "Inspection report", cases: "Corrective actions", audit: "Audit log", users: "Users", account: "My account" },
    pS: { overview: "Safety signal across sites: findings, severity, and open and overdue corrective actions.",
      inspect: "Photos or video plus the inspector's note — a full report in about 30 seconds.",
      live: "Frames arrive in sequence, violations are flagged the moment they appear, and finishing produces the full report.",
      inspections: "Every completed inspection — search, filter and open any report.",
      report: "An evidence-grounded report — every finding tied to its frame, never closed without human approval.",
      cases: "Every corrective-action case across inspections, ordered by urgency and deadline.",
      audit: "Every case action — assign, verify, approve, notes — recorded and never deleted.",
      users: "Inspector accounts and roles — admin only.", account: "Your profile, preferences and password." },
    ctaNew: "New inspection", siteFilter: "Site", siteAll: "All sites",
    seedNote: "These figures include demo seed data; real inspections replace it automatically as they accumulate.",
    aTotal: "Inspections", dTotal: "Recorded inspections", aFindings: "Findings", dFindings: (n) => `${n} per inspection on average`,
    aHigh: "High severity", dHigh: "Need immediate action", aOpen: "Open cases", dOpen: (r) => `${r}% closure rate`,
    aOverdue: "Overdue", dOverdue: "Past their deadline",
    trendT: "Daily activity", trendN: (n) => `${n} inspections in 14 days`, legInsp: "Inspections", legFind: "Findings",
    sevMix: "Severity mix", sevTotal: (n) => `${n} finding${n === 1 ? "" : "s"}`, topHazards: "Most frequent hazards",
    agingT: "Cases needing follow-up", viewAll: "View all", recent: "Recent inspections",
    pipeT: "From walkthrough to verified closure", pipeHint: "Every inspection runs the same loop — and a finding is never closed without human approval.",
    loop: [["Observe", "Photos, video or a live feed"], ["Understand", "Scene segmentation with Meta models"], ["Explain", "Arabic report with evidence"],
      ["Act", "A case for every finding"], ["Verify", "Re-inspect with new evidence"], ["Close", "Human approval only"]],
    noData: "No data yet.", demo: "Demo", times: (n) => `${n}×`,
    newInspect: "New inspection", newHint: "A full report in about 30 seconds",
    dropTitle: "Drop photos or video here, or click to choose", dropSub: "JPG · PNG · WEBP · MP4 · MOV — up to 150 MB",
    notes: "Inspector notes (transcribed voice or written)", notesPh: "Example: I noticed a worker near the upper edge, and the forklift operates close to the pedestrian area…",
    micRec: "Record voice note", micStop: "Stop recording", micListening: "Listening… speak now.",
    micDone: "Transcript added to notes.", micErr: "Voice transcription unavailable — type the note instead.",
    ctx: "Site / inspection context", ctxPh: "Example: factory — weekly safety inspection",
    run: "Generate report", clear: "Clear", running: "Baseer is analyzing the site…",
    progress: ["Uploading evidence", "Extracting frames", "Analyzing the scene", "Writing the report"],
    needInput: "Add a photo, a video or a written note first.", done: "Report generated.", error: "Could not generate the report.",
    guideT: "What does Baseer check?",
    guide: ["PPE: helmet, hi-vis vest, gloves, eye protection.", "Movement hazards: forklift paths, upper edges, guard rails.",
      "Machine hazards: guards, emergency exits, floor markings."],
    guideNote: "The report rests only on what is visible in the frame — what cannot be determined is recorded as such, and uncertainty never raises severity.",
    howT: "How does an inspection work?",
    how: [["Evidence", "Upload photos or a short video and add your note."], ["Understanding", "Scenes are segmented and hazards reasoned with your note."],
      ["Report", "Findings with severity, frame and corrective action."], ["Follow-up", "Every finding opens a case tracked to closure."]],
    stageIdle: "Camera is off — start a session, then turn on the camera or send a frame from a file.",
    kLiveState: "Status", liveFrames: "Frames received", liveAlertsT: "Alerts", liveOn: "Live", liveIdle: "Idle",
    liveStart: "Start live session", liveCamT: "Turn camera on", camStop: "Turn camera off", liveSendFile: "Send frame from file",
    liveFinish: "Finish & generate report", resumeHint: "Unfinished sessions:", resume: "Resume",
    liveCtx: "Site", liveHint: "Sampled near-real-time analysis — a snapshot every 3 seconds; each violation alerts on first sight.",
    liveStarted: "Live session started.", camDenied: "Camera unavailable — send a frame from a file instead.",
    camOn: "Camera on — a snapshot every 3 seconds.", frames: (n) => `${n} frame${n === 1 ? "" : "s"}`,
    alertsT: "Live alerts", alertsN: (n) => `${n} alert${n === 1 ? "" : "s"}`, noAlerts: "No alerts yet — they appear here the moment a violation is seen.",
    frameN: (i) => `Frame ${i + 1}`, finishing: "Generating the report…",
    histSearchPh: "Search by ID, site or hazard…", csvBtn: "Export CSV", sevAll: "All severities",
    colId: "Inspection", colDate: "Date", thSite: "Site", colSource: "Source", colFindings: "Findings", colCases: "Cases",
    histEmpty: "No matching inspections.", srcUpload: "Upload", srcLive: "Live camera",
    closedOf: (c, t) => `${c}/${t} closed`,
    noReport: "No report open yet", noReportHint: "Run a new inspection, or open a report from the inspection history.",
    report: "Report", pdfRep: "PDF", printRep: "Print", shareWa: "WhatsApp", copyLink: "Copy link", linkCopied: "Report link copied.",
    tEvidence: "Attached evidence", findings: "Findings", findingsN: (n) => `${n} finding${n === 1 ? "" : "s"}`, noFindings: "No findings — nothing requiring action was observed.",
    meta: (r) => `${fmtTime(r.created_at)} · ${r.frames_processed} frame${r.frames_processed === 1 ? "" : "s"} · Site: ${siteName(r)}`,
    stripTotal: "Findings", noEvidence: "No attached files — report based on the inspector's note.",
    more: (n) => `+${n} more`, loadVideo: "Play video",
    action: "Corrective action", frame: (i) => `Frame ${i + 1}`,
    srcSeg: "Visual model", srcInsp: "Inspector note", srcBoth: "Model + inspector", detUncertain: "Unable to determine",
    sev: { high: "High", medium: "Medium", low: "Low" },
    pipeBadgeMock: "Demo data", pipeBadgeVision: "Muse vision", pipeBadgeSam: "SAM 3.1",
    caseT: "Corrective action", due: (d) => `Due ${d}`, overdue: "Overdue",
    steps: ["Open", "Assigned", "Verified", "Closed"],
    status: { open: "Open", assigned: "Assigned", closed: "Closed", overdue: "Overdue" },
    assignPh: "Assign to…", assign: "Assign", verify: "AI verify", verPhoto: "Re-inspection evidence", approve: "Approve closure",
    roles: ["Safety Supervisor", "Site Manager", "Contractor"],
    approveQ: "Approve closing this case?", approveBody: "The closure is recorded under your name in the audit log and cannot be undone.",
    activity: (n) => `Activity (${n})`, notePh: "Add a note to the case log…", noteAdd: "Add",
    act: { assign: "Assign", verify: "Verify", approve: "Approve closure", verify_evidence: "Verify with evidence", note: "Note" },
    assigned: "Case assigned.", verified: "Verification complete.", closed: "Case closed.", noteSaved: "Note added.",
    briefT: "Crew briefing", briefHint: "A short toolbox talk from this report, in the crew's language, to read aloud",
    briefPick: "Pick the crew's language to write the briefing.", briefCopy: "Copy", briefRead: "Read aloud", briefRedo: "Regenerate",
    briefCopied: "Briefing copied.", briefNoVoice: (n) => `No ${n} voice on this device.`, briefWorking: "Baseer is writing the briefing…",
    segToggle: (src, n, on) => `SAM 3.1 segments (${n}) · ${on ? "hide" : "show"}`,
    chat: "Ask Baseer", chatHint: "Answers grounded strictly in this inspection's evidence.", chatPh: "Ask about a finding or request a draft notice…",
    send: "Send", chatErr: "Couldn't answer just now.",
    chips: (f) => [f ? `Why is "${f.title_en || f.title_ar}" ${(S.en.sev[f.severity] || "").toLowerCase()} severity?` : "What is the most serious finding?",
      "Draft a notice to the contractor", "Summarize for the site manager"],
    tabs: { all: "All", open: "Open", assigned: "Assigned", overdue: "Overdue", closed: "Closed" },
    colCase: "Case", colCaseSev: "Severity", colStatus: "Status", colAssignee: "Owner", colDue: "Deadline",
    casesEmpty: "No cases here — all under control.", unassigned: "Unassigned",
    dueIn: (d) => d <= 0 ? "today" : `in ${d}d`, dueAgo: (d) => `${d}d overdue`,
    auditSearchPh: "Search the log…", actAll: "All actions",
    thTime: "Time", thAuditId: "Inspection", thFindingN: "Finding #", thAction: "Action", thActor: "Actor", thDetail: "Detail",
    auditEmpty: "No recorded actions yet.",
    tUsers: "Users", usersN: (n) => `${n} account${n === 1 ? "" : "s"}`, thUName: "User", thURole: "Role", thUCreated: "Created",
    tNewUser: "New account", tNuName: "Username", tNuPass: "Password (8+ characters)", tNuRole: "Role", nuAdd: "Add user",
    userAdded: "User added.", roleSaved: "Role updated.", resetPw: "Reset password",
    resetQ: (u) => `New password for ${u}`, resetBody: "At least 8 characters. Share it with the user over a secure channel.", pwReset: "Password reset.",
    delUser: "Delete", delQ: (u) => `Delete user ${u}?`, delBody: "They will no longer be able to sign in. The audit log is kept as is.", userDeleted: "User deleted.",
    you: "you",
    prefLang: "Language", prefLangHint: "Interface and report display language.", prefTheme: "Appearance", prefThemeHint: "Light or dark.",
    light: "Light", dark: "Dark",
    tMyPass: "Change password", tPwOld: "Current password", tPwNew: "New password (8+)", pwChange: "Update password",
    pwOk: "Password changed.", pwErr: "Change failed — check your current password.",
    about: (h) => `Baseer ${h.version || ""} by Veebase · Mode: ${h.mode === "live" ? "live" : "demo"} · © ${new Date().getFullYear()} Veebase`,
    modeLive: "LIVE", modeMock: "DEMO", modeLiveS: "Meta models connected", modeMockS: "Synthetic outputs, no API keys",
    ok: "OK", cancel: "Cancel", confirm: "Confirm", notFound: "Report not found.", genericErr: "Something went wrong.",
    seedRow: "Demo seed record — no full report behind it.",
  },
};
const ROLE_KEYS = ["Safety Supervisor", "Site Manager", "Contractor", "Admin"];
const ROLE_AR = { "Safety Supervisor": "مشرف السلامة", "Site Manager": "مدير الموقع", Contractor: "المقاول", Admin: "مدير النظام" };

/* ------------------------------------------------------------------ state */
const $ = (id) => document.getElementById(id);
const store = {
  get(k, d = null) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  del(k) { try { localStorage.removeItem(k); } catch (e) { /* private mode */ } },
};
const qs = new URLSearchParams(location.search);
let lang = qs.get("lang") === "en" ? "en" : (store.get("baseer_lang") || "ar");
let session = store.get("baseer_session");
let health = { mode: "mock", sla_days: { high: 1, medium: 7, low: 30 } };
let currentView = "overview";
let sites = [];
let booted = false;
const T = () => S[lang];
const pick = (o, k) => (lang === "ar" ? (o[k + "_ar"] || o[k + "_en"]) : (o[k + "_en"] || o[k + "_ar"])) || "";

function esc(t) {
  return String(t ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function fmtTime(ts) {
  if (!ts) return "";
  try { return new Date(ts).toLocaleString(lang === "ar" ? "ar-u-nu-latn" : "en-GB", { dateStyle: "medium", timeStyle: "short" }); }
  catch (e) { return String(ts).slice(0, 16).replace("T", " "); }
}
function fmtDate(ts) {
  try { return new Date(ts).toLocaleDateString(lang === "ar" ? "ar-u-nu-latn" : "en-GB", { day: "numeric", month: "short" }); }
  catch (e) { return String(ts).slice(5, 10); }
}
function fmtSize(n) { return n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"; }
function fmtNum(n) { return Number(n || 0).toLocaleString(lang === "ar" ? "ar-u-nu-latn" : "en-US"); }
function siteName(r) { return ((r.site_context || r.site || "").trim()) || "general"; }
function roleName(r) { return lang === "ar" ? (ROLE_AR[r] || r) : r; }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
// SAM segment labels arrive snake_case ("guard_rail_missing").
const humanize = (label) => { const t = String(label || "").replace(/_/g, " ").trim(); return t.charAt(0).toUpperCase() + t.slice(1); };
const isVideo = (name) => /\.(mp4|mov|webm|mkv)$/i.test(name || "");

/* -------------------------------------------------------------------- api */
class ApiError extends Error { constructor(status, detail) { super(detail); this.status = status; } }
async function api(path, { method = "GET", json, form, raw = false } = {}) {
  const headers = {};
  if (session && session.token) headers.Authorization = "Bearer " + session.token;
  let body;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  const res = await fetch(path, { method, headers, body });
  // 401 means an expired session, except where it answers a credential check.
  if (res.status === 401 && session && !["/auth/login", "/auth/password"].includes(path)) {
    logout(); throw new ApiError(401, "login required");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) { /* not JSON */ }
    throw new ApiError(res.status, String(detail));
  }
  return raw ? res : res.json();
}
async function downloadFile(path, filename) {
  try {
    const res = await api(path, { raw: true });
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch (e) { toast(e.message, "err"); }
}

/* ------------------------------------------------- toasts, modal, lightbox */
function toast(msg, kind = "ok") {
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.innerHTML = ic(kind === "err" ? "alert" : kind === "info" ? "info" : "check") + `<span>${esc(msg)}</span>`;
  $("toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 300); }, kind === "err" ? 5200 : 3200);
}
function modal({ title, body = "", ok, danger = false, input = false }) {
  const d = $("modal");
  $("modalTitle").textContent = title;
  $("modalBody").textContent = body;
  $("modalOk").textContent = ok || T().confirm;
  $("modalOk").className = "btn " + (danger ? "btn-danger" : "btn-primary");
  $("modalCancel").textContent = T().cancel;
  const inp = $("modalInput");
  inp.value = ""; inp.classList.toggle("hidden", !input);
  return new Promise((resolve) => {
    d.onclose = () => resolve(d.returnValue === "ok" ? (input ? inp.value : true) : null);
    d.showModal();
    if (input) inp.focus();
  });
}
function lightbox(src, segs = []) {
  $("lightboxImg").src = src;
  $("lightboxSegs").innerHTML = segLayer(segs);
  $("lightbox").classList.remove("hidden");
}
// SAM 3.1 segments: normalized [x, y, w, h] boxes per extracted frame.
const HAZARD_HINTS = ["without", "missing", "no_", "_no"];
let showSegs = store.get("baseer_segs", true);
// Only real SAM output is drawn: demo-mode segments are synthetic boxes that
// would land on real photos as nonsense.
function samSegments(r) { return r.segmentation_source === "sam" ? (r.segments || []) : []; }
function segsFor(r, frameIdx) {
  return samSegments(r).filter((sg) => sg.frame_index === frameIdx && (sg.bbox || []).length === 4);
}
function segLayer(segs) {
  return segs.map((sg) => {
    const [x, y, w, h] = sg.bbox.map((v) => Math.max(0, Math.min(1, v)) * 100);
    const hazard = HAZARD_HINTS.some((k) => String(sg.label).toLowerCase().includes(k));
    const label = lang === "ar" ? (sg.label_ar || humanize(sg.label)) : humanize(sg.label);
    return `<div class="seg-box${hazard ? " hazard" : ""}${y < 6 ? " low" : ""}" style="left:${x}%;top:${y}%;width:${w}%;height:${h}%"><span>${esc(label)}</span></div>`;
  }).join("");
}
$("lightbox").addEventListener("click", () => $("lightbox").classList.add("hidden"));
$("modalCancel").addEventListener("click", () => $("modal").close("cancel"));

/* ------------------------------------------------------- language + theme */
function applyLang() {
  const s = T();
  document.documentElement.lang = lang;
  document.documentElement.dir = s.dir;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const v = s[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = s[el.dataset.i18nPh] || ""; });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = s[el.dataset.i18nTitle] || ""; el.setAttribute("aria-label", el.title);
  });
  document.querySelectorAll("[data-lang]").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
  $("guideList").innerHTML = s.guide.map((g) => `<li>${ic("check")}<span>${esc(g)}</span></li>`).join("");
  $("howSteps").innerHTML = s.how.map((h, i) => `<li><span class="n">${i + 1}</span><div><b>${esc(h[0])}</b><small>${esc(h[1])}</small></div></li>`).join("");
  $("loopSteps").innerHTML = s.loop.map((l, i) => `<li><span>0${i + 1}</span><b>${esc(l[0])}</b><small>${esc(l[1])}</small></li>`).join("");
  $("nuRole").innerHTML = ROLE_KEYS.map((r) => `<option value="${r}">${esc(roleName(r))}</option>`).join("");
  $("micLabel").textContent = micRec ? s.micStop : s.micRec;
  paintMode(); paintUser(); paintSiteOptions(); paintLive(); paintAssigneeList();
  if (booted) renderRoute();
}
function setLang(l) { lang = l; store.set("baseer_lang", l); applyLang(); }
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  store.set("baseer_theme", t);
  try { localStorage.setItem("baseer_theme", t); } catch (e) { /* private mode */ }
  paintThemeButtons();
  if (currentView === "overview") loadOverview();
}
function paintThemeButtons() {
  const t = document.documentElement.dataset.theme;
  document.querySelectorAll("[data-theme-toggle] i").forEach((i) => { i.dataset.icon = t === "dark" ? "sun" : "moon"; });
  document.querySelectorAll("[data-set-theme]").forEach((b) => b.classList.toggle("active", b.dataset.setTheme === t));
  paintIcons();
}
document.addEventListener("click", (e) => {
  const l = e.target.closest("[data-lang]"); if (l) setLang(l.dataset.lang);
  const th = e.target.closest("[data-theme-toggle]");
  if (th) setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  const st = e.target.closest("[data-set-theme]"); if (st) setTheme(st.dataset.setTheme);
  const pw = e.target.closest("[data-toggle-pw]");
  if (pw) { const inp = $(pw.dataset.togglePw); inp.type = inp.type === "password" ? "text" : "password"; }
});

/* ------------------------------------------------------------------- auth */
$("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("loginErr"), btn = $("loginBtn");
  err.classList.add("hidden"); btn.disabled = true;
  try {
    session = await api("/auth/login", { method: "POST", json: { username: $("loginUser").value.trim(), password: $("loginPass").value } });
    store.set("baseer_session", session);
    $("loginPass").value = "";
    paintUser();
    refreshSites();
    if (!location.hash || location.hash === "#/login") location.hash = "#/overview"; else renderRoute();
    refreshBadges();
  } catch (ex) {
    err.textContent = ex.status === 429 ? T().loginThrottled : T().loginErr;
    err.classList.remove("hidden");
  } finally { btn.disabled = false; }
});
function logout() {
  session = null;
  store.del("baseer_session");
  if (liveSessionId) stopCamera();
  paintUser();
}
$("logoutBtn").addEventListener("click", () => { logout(); history.replaceState(null, "", "#/overview"); });
function paintUser() {
  document.body.classList.toggle("gated", !session);
  if (!session) { setTimeout(() => $("loginUser").focus(), 50); return; }
  const initials = (session.username || "?").slice(0, 2);
  $("userAvatar").textContent = initials; $("accAvatar").textContent = initials;
  $("userName").textContent = session.username; $("accName").textContent = session.username;
  $("userRole").textContent = roleName(session.role); $("accRole").textContent = roleName(session.role);
  $("navUsers").classList.toggle("hidden", session.role !== "Admin");
}
function paintMode() {
  const s = T(), live = health.mode === "live";
  for (const b of [$("modeBadge"), $("loginMode")]) { b.className = "badge " + (live ? "live" : "mock"); b.textContent = live ? s.modeLive : s.modeMock; }
  $("modeCard").className = "mode-card " + (live ? "live" : "mock");
  $("modeCardT").textContent = live ? s.modeLive : s.modeMock;
  $("modeCardS").textContent = live ? s.modeLiveS : s.modeMockS;
  $("aboutLine").textContent = s.about(health);
}
async function loadHealth() {
  try { health = Object.assign(health, await (await fetch("/health")).json()); } catch (e) { /* offline: keep defaults */ }
  paintMode();
}

/* ----------------------------------------------------------------- router */
function parseRoute() {
  const [path, query] = (location.hash.replace(/^#\/?/, "") || "overview").split("?");
  const parts = path.split("/");
  return { view: parts[0] || "overview", param: decodeURIComponent(parts[1] || ""), query: new URLSearchParams(query || "") };
}
const VIEWS = ["overview", "inspect", "live", "inspections", "report", "cases", "audit", "users", "account"];
function renderRoute() {
  if (!session) return;
  let { view, param, query } = parseRoute();
  if (!VIEWS.includes(view)) view = "overview";
  if (view === "users" && session.role !== "Admin") view = "overview";
  currentView = view;
  const s = T();
  for (const v of VIEWS) $("view-" + v).classList.toggle("hidden", v !== view);
  document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === view));
  $("crumb").textContent = `${s.crumb} / ${s.pT[view]}`;
  $("pageTitle").textContent = s.pT[view];
  $("pageSub").textContent = s.pS[view];
  document.title = `${s.pT[view]} · Baseer by Veebase`;
  document.body.classList.remove("nav-open");
  ({
    overview: loadOverview, inspect: paintThumbs, live: () => { paintLive(); paintResumeRow(!!liveSessionId); }, inspections: () => loadHistory(query),
    report: () => openReport(param, query.get("f")), cases: () => loadCases(query.get("status")),
    audit: loadAudit, users: loadUsers, account: () => {},
  })[view]();
  paintIcons();
}
window.addEventListener("hashchange", renderRoute);
const go = (hash) => { if (location.hash === hash) renderRoute(); else location.hash = hash; };

$("menuBtn").addEventListener("click", () => document.body.classList.toggle("nav-open"));
$("scrim").addEventListener("click", () => document.body.classList.remove("nav-open"));
$("globalSearch").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("globalQ").value.trim();
  if (!q) return;
  if (/^[0-9a-f]{12}$/i.test(q)) {
    try { await api("/inspections/" + q); $("globalQ").value = ""; return go("#/report/" + q); } catch (ex) { /* fall through to search */ }
  }
  go("#/inspections?q=" + encodeURIComponent(q));
});
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && session && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); $("globalQ").focus(); }
  if (e.key === "Escape") { $("lightbox").classList.add("hidden"); document.body.classList.remove("nav-open"); }
});

/* ------------------------------------------------------------ sites/badges */
async function refreshSites() {
  try { sites = (await api("/sites")).sites || []; } catch (e) { sites = []; }
  paintSiteOptions();
}
function paintSiteOptions() {
  const s = T();
  const opts = (cur) => `<option value="">${esc(s.siteAll)}</option>` +
    sites.map((o) => `<option value="${esc(o.site)}"${o.site === cur ? " selected" : ""}>${esc(o.site)} (${o.inspections})</option>`).join("");
  $("siteFilter").innerHTML = opts(overviewSite);
  $("histSite").innerHTML = opts(histState.site);
  $("caseSite").innerHTML = opts(caseState.site);
  $("siteList").innerHTML = sites.filter((o) => o.site !== "general").map((o) => `<option value="${esc(o.site)}">`).join("");
  $("histSev").innerHTML = `<option value="">${esc(s.sevAll)}</option>` +
    ["high", "medium", "low"].map((k) => `<option value="${k}"${histState.severity === k ? " selected" : ""}>${esc(s.sev[k])}</option>`).join("");
  $("auditAction").innerHTML = `<option value="">${esc(s.actAll)}</option>` +
    Object.entries(s.act).map(([k, v]) => `<option value="${k}"${auditState.action === k ? " selected" : ""}>${esc(v)}</option>`).join("");
}
async function refreshBadges() {
  try {
    const a = await api("/analytics");
    const n = a.cases.open + a.cases.assigned;
    $("navCasesCount").textContent = n;
    $("navCasesCount").classList.toggle("hidden", !n);
  } catch (e) { /* badge is decoration */ }
}

/* --------------------------------------------------------------- overview */
let overviewSite = "";
$("siteFilter").addEventListener("change", (e) => { overviewSite = e.target.value; loadOverview(); });
async function loadOverview() {
  let a;
  try { a = await api("/analytics" + (overviewSite ? "?site=" + encodeURIComponent(overviewSite) : "")); }
  catch (e) { return; }
  const s = T();
  $("seedNotice").classList.toggle("hidden", !a.demo_seed_included);
  $("vTotal").textContent = fmtNum(a.total_inspections);
  $("vFindings").textContent = fmtNum(a.total_findings);
  $("dFindings").textContent = s.dFindings(a.total_inspections ? (a.total_findings / a.total_inspections).toFixed(1) : 0);
  $("vHigh").textContent = fmtNum(a.by_severity.high);
  $("vOpen").textContent = fmtNum(a.cases.open + a.cases.assigned);
  $("dOpen").textContent = s.dOpen(Math.round(a.cases.closure_rate * 100));
  $("vOverdue").textContent = fmtNum(a.cases.overdue);
  renderTrend(a.trend || []);
  renderDonut(a.by_severity, a.total_findings);
  const mx = Math.max(1, ...a.top_hazards.map((h) => h.count));
  $("hazardBars").innerHTML = a.top_hazards.map((h) =>
    `<div><div class="hbar-label"><span>${esc(pick(h, "title"))}</span><b>${esc(s.times(h.count))}</b></div>` +
    `<div class="hbar-track"><div class="hbar-fill" style="width:${(100 * h.count / mx).toFixed(1)}%"></div></div></div>`).join("") ||
    `<p class="muted">${esc(s.noData)}</p>`;
  $("agingList").innerHTML = (a.open_cases || []).slice(0, 6).map((c) => {
    const dl = dueLabel(c);
    return `<div class="list-item" data-href="#/report/${esc(c.inspection_id)}?f=${c.finding_index}">
      <span class="li-icon">${ic(c.overdue ? "clock" : "clipboard")}</span>
      <div class="li-main"><b>${esc(pick(c, "title"))}</b><small><span class="mono">${esc(c.inspection_id)}</span> · ${esc(c.assignee || s.unassigned)}</small></div>
      <span class="sev ${c.severity}">${esc(s.sev[c.severity])}</span>
      <small class="${c.overdue ? "c-high" : "muted"}" style="white-space:nowrap">${esc(dl)}</small>
      <span class="chev">${ic("chevron")}</span></div>`;
  }).join("") || `<p class="muted">${esc(s.noData)}</p>`;
  $("recentList").innerHTML = (a.recent || []).map((r) =>
    `<div class="list-item" data-href="${r.seed ? "" : "#/report/" + esc(r.inspection_id)}">
      <span class="li-icon">${ic("file")}</span>
      <div class="li-main"><b><span class="mono">${esc(r.inspection_id)}</span>${r.seed ? ` <span class="badge demo">${esc(s.demo)}</span>` : ""}</b>
        <small>${esc(fmtTime(r.created_at))} · ${ic("pin")} ${esc(r.site)}</small></div>
      <span class="mini-sev"><span class="sev high">${r.high}</span></span>
      <small class="muted">${esc(s.findingsN(r.findings))}</small>
      <span class="chev">${ic("chevron")}</span></div>`).join("") || `<p class="muted">${esc(s.noData)}</p>`;
}
document.addEventListener("click", (e) => {
  const li = e.target.closest("[data-href]");
  if (!li) return;
  if (li.dataset.href) go(li.dataset.href); else toast(T().seedRow, "info");
});
function renderTrend(trend) {
  const s = T(), days = trend.slice(-14);
  $("trendTotal").textContent = s.trendN(days.reduce((n, d) => n + d.inspections, 0));
  if (!days.length) { $("trendChart").innerHTML = `<p class="muted">${esc(s.noData)}</p>`; return; }
  const W = 640, H = 200, padB = 24, padT = 10, mx = Math.max(1, ...days.map((d) => d.findings), ...days.map((d) => d.inspections));
  const step = W / days.length, bw = Math.min(16, step / 3.2);
  const y = (v) => H - padB - (H - padB - padT) * v / mx;
  const rtl = lang === "ar";
  let g = "";
  for (let k = 0; k <= 3; k++) {
    const yy = padT + (H - padB - padT) * k / 3;
    g += `<line class="grid-line" x1="0" x2="${W}" y1="${yy}" y2="${yy}"/>`;
  }
  days.forEach((d, i) => {
    const cx = rtl ? W - step * (i + 0.5) : step * (i + 0.5);
    g += `<g><title>${d.day}: ${d.inspections} / ${d.findings}</title>
      <rect class="bar-2" x="${cx - bw - 1}" y="${y(d.inspections)}" width="${bw}" height="${H - padB - y(d.inspections)}" rx="3"/>
      <rect class="bar" x="${cx + 1}" y="${y(d.findings)}" width="${bw}" height="${H - padB - y(d.findings)}" rx="3"/>
      ${i % 2 === 0 || days.length < 8 ? `<text class="axis" x="${cx}" y="${H - 6}" text-anchor="middle">${esc(fmtDate(d.day + "T12:00:00"))}</text>` : ""}</g>`;
  });
  $("trendChart").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg>
    <div class="chart-legend"><span><i style="background:var(--brand)"></i>${esc(s.legInsp)}</span><span><i style="background:var(--accent)"></i>${esc(s.legFind)}</span></div>`;
}
function renderDonut(sev, total) {
  const s = T(), R = 52, C = 2 * Math.PI * R;
  const parts = [["high", "var(--high)"], ["medium", "var(--med)"], ["low", "var(--low)"]];
  let off = 0, arcs = "";
  for (const [k, color] of parts) {
    const frac = total ? sev[k] / total : 0;
    if (frac > 0) arcs += `<circle r="${R}" cx="70" cy="70" fill="none" stroke="${color}" stroke-width="16" stroke-dasharray="${(frac * C).toFixed(2)} ${C.toFixed(2)}" stroke-dashoffset="${(-off * C).toFixed(2)}" transform="rotate(-90 70 70)"/>`;
    off += frac;
  }
  $("sevTotal").textContent = s.sevTotal(total);
  $("sevDonut").innerHTML = `<svg viewBox="0 0 140 140"><circle r="${R}" cx="70" cy="70" fill="none" stroke="var(--surface-3)" stroke-width="16"/>${arcs}
    <text class="donut-n" x="70" y="72" text-anchor="middle">${fmtNum(total)}</text><text class="donut-l" x="70" y="90" text-anchor="middle">${esc(s.stripTotal)}</text></svg>`;
  $("sevLegend").innerHTML = parts.map(([k, color]) =>
    `<div><i style="background:${color}"></i><span>${esc(s.sev[k])}</span><b>${fmtNum(sev[k])}</b><small>${total ? Math.round(100 * sev[k] / total) : 0}%</small></div>`).join("");
}

/* -------------------------------------------------------- new inspection */
let pendingFiles = [];
const dz = $("dropZone");
dz.addEventListener("click", () => $("files").click());
dz.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("files").click(); } });
$("files").addEventListener("change", (e) => { addFiles(e.target.files); e.target.value = ""; });
["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("over"); }));
dz.addEventListener("drop", (e) => { if (e.dataTransfer && e.dataTransfer.files.length) addFiles(e.dataTransfer.files); });
function addFiles(list) {
  for (const f of list) {
    if (!/^(image|video)\//.test(f.type) && !/\.(jpe?g|png|webp|mp4|mov|webm|mkv)$/i.test(f.name)) continue;
    pendingFiles.push({ file: f, url: URL.createObjectURL(f), kind: isVideo(f.name) || f.type.startsWith("video") ? "video" : "image" });
  }
  paintThumbs();
}
function paintThumbs() {
  $("thumbs").innerHTML = pendingFiles.map((p, i) => `<div class="thumb">
    ${p.kind === "video" ? `<video src="${p.url}" muted preload="metadata"></video><span class="thumb-kind">VIDEO</span>` : `<img src="${p.url}" alt="">`}
    <button type="button" class="thumb-x" data-rm="${i}" aria-label="Remove">${ic("x")}</button>
    <span class="thumb-meta">${esc(p.file.name)} · ${fmtSize(p.file.size)}</span></div>`).join("");
}
$("thumbs").addEventListener("click", (e) => {
  const b = e.target.closest("[data-rm]");
  if (!b) return;
  const [p] = pendingFiles.splice(+b.dataset.rm, 1);
  URL.revokeObjectURL(p.url);
  paintThumbs();
});
$("notes").addEventListener("input", () => { $("notesCount").textContent = `${$("notes").value.length} / 5000`; });
$("clearBtn").addEventListener("click", () => {
  pendingFiles.forEach((p) => URL.revokeObjectURL(p.url));
  pendingFiles = []; $("notes").value = ""; $("ctx").value = ""; $("notesCount").textContent = "0 / 5000";
  paintThumbs();
});
$("inspForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const s = T();
  if (!pendingFiles.length && !$("notes").value.trim() && health.mode === "live") return toast(s.needInput, "err");
  const fd = new FormData();
  for (const p of pendingFiles) fd.append("files", p.file);
  fd.append("notes", $("notes").value);
  fd.append("site_context", $("ctx").value.trim());
  const stop = showProgress();
  $("runBtn").disabled = true;
  try {
    const rep = await api("/inspections", { method: "POST", form: fd });
    await stop(true);
    // Keep the just-uploaded files as the report's local evidence (no refetch).
    localMedia.set(rep.inspection_id, pendingFiles.map((p) => ({ name: p.file.name, kind: p.kind, url: p.url, size: p.file.size })));
    pendingFiles = []; $("notes").value = ""; $("notesCount").textContent = "0 / 5000"; paintThumbs();
    report = rep;
    toast(s.done);
    refreshSites(); refreshBadges();
    go("#/report/" + rep.inspection_id);
  } catch (ex) {
    await stop(false);
    toast(`${s.error} ${ex.message || ""}`, "err");
  } finally { $("runBtn").disabled = false; }
});
function showProgress() {
  const s = T(), el = $("analyzing"), list = $("progressSteps");
  list.innerHTML = s.progress.map((p) => `<li><span class="ps"></span><span>${esc(p)}</span></li>`).join("");
  el.classList.remove("hidden");
  const items = [...list.children];
  let i = 0;
  const mark = () => items.forEach((li, k) => {
    li.className = k < i ? "done" : k === i ? "active" : "";
    li.querySelector(".ps").innerHTML = k < i ? ic("check") : "";
  });
  mark();
  // Stages advance on a timer while the single request runs; the last one
  // waits for the server so the overlay never claims completion early.
  const timer = setInterval(() => { if (i < items.length - 1) { i++; mark(); } }, 1400);
  return async (ok) => {
    clearInterval(timer);
    if (ok) { i = items.length; mark(); await new Promise((r) => setTimeout(r, 450)); }
    el.classList.add("hidden");
  };
}

/* ---- voice note (Meta transcription proxy; typed notes are the fallback) */
let micRec = null, micWS = null;
$("micBtn").addEventListener("click", async () => {
  const s = T();
  if (micRec) { micRec.stop(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { $("micStatus").textContent = s.micErr; return; }
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
  catch (e) { $("micStatus").textContent = s.micErr; return; }
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  micWS = new WebSocket(`${proto}//${location.host}/voice/transcribe?token=${encodeURIComponent(session ? session.token : "")}`);
  const reset = () => { micRec = null; $("micLabel").textContent = T().micRec; $("micBtn").classList.remove("btn-accent"); };
  micWS.onmessage = (ev) => {
    try {
      const m = JSON.parse(ev.data);
      if (m.type === "final" && m.text) {
        const box = $("notes");
        box.value = (box.value ? box.value + " " : "") + m.text;
        box.dispatchEvent(new Event("input"));
        $("micStatus").textContent = s.micDone;
      } else if (m.type === "partial" && m.text) $("micStatus").textContent = m.text;
      else if (m.type === "error") $("micStatus").textContent = s.micErr;
    } catch (e) { /* ignore non-JSON frames */ }
  };
  micWS.onerror = () => { $("micStatus").textContent = s.micErr; stream.getTracks().forEach((t) => t.stop()); reset(); };
  micWS.onclose = () => { if (micRec && micRec.state !== "inactive") micRec.stop(); else stream.getTracks().forEach((t) => t.stop()); reset(); };
  micWS.onopen = () => {
    micRec = new MediaRecorder(stream);
    micRec.ondataavailable = (e) => { if (e.data.size && micWS.readyState === 1) micWS.send(e.data); };
    micRec.onstop = () => { stream.getTracks().forEach((t) => t.stop()); try { micWS.close(); } catch (e) { /* closed */ } reset(); };
    micRec.start(500);
    $("micLabel").textContent = s.micStop; $("micBtn").classList.add("btn-accent");
    $("micStatus").textContent = s.micListening;
  };
});

/* ------------------------------------------------------------ live camera */
let liveSessionId = null, liveAlerts = [], liveFrames = 0, liveStartedAt = 0, liveClockTimer = null;
let camStream = null, camTimer = null;
function paintLive() {
  const s = T(), on = !!liveSessionId;
  $("vLiveState").textContent = on ? s.liveOn : s.liveIdle;
  $("vLiveState").className = on ? "c-low" : "";
  $("vLiveFrames").textContent = fmtNum(liveFrames);
  $("vLiveAlerts").textContent = fmtNum(liveAlerts.length);
  $("alertsCount").textContent = s.alertsN(liveAlerts.length);
  $("liveStart").classList.toggle("hidden", on);
  $("liveFinish").classList.toggle("hidden", !on);
  $("liveFileBtn").classList.toggle("hidden", !on);
  $("livePill").classList.toggle("hidden", !on);
  $("navLiveDot").classList.toggle("hidden", !on);
  $("liveCamLabel").textContent = camStream ? s.camStop : s.liveCamT;
  $("stageCount").textContent = on ? s.frames(liveFrames) : "";
  $("stageEmpty").classList.toggle("hidden", !!camStream);
  $("liveAlerts").innerHTML = liveAlerts.length ? liveAlerts.slice().reverse().map((a) =>
    `<div class="alert"><span class="li-icon">${ic("alert")}</span><div><b>${esc(lang === "ar" ? a.label_ar || a.message_ar : humanize(a.label) || a.message_en)}</b>
      <small>${esc(s.frameN(a.frame_index))} · ${esc(a._at ? new Date(a._at).toLocaleTimeString(lang === "ar" ? "ar-u-nu-latn" : "en-GB") : "")}${a.source === "yolo" ? " · YOLO " + Math.round((a.confidence || 0) * 100) + "%" : ""}</small></div></div>`).join("")
    : `<div class="empty">${ic("check-shield")}<span>${esc(s.noAlerts)}</span></div>`;
}
async function paintResumeRow(hide) {
  const row = $("resumeRow");
  if (hide || !session) { row.classList.add("hidden"); return; }
  try {
    const l = (await api("/live/sessions")).sessions || [];
    row.classList.toggle("hidden", !l.length);
    $("resumeSel").innerHTML = l.map((x) => `<option value="${esc(x.session_id)}">${esc(x.session_id.slice(0, 8))} · ${esc(x.site_context || "general")} · ${x.frames_received}f</option>`).join("");
  } catch (e) { row.classList.add("hidden"); }
}
function startClock() {
  liveStartedAt = Date.now();
  clearInterval(liveClockTimer);
  liveClockTimer = setInterval(() => {
    const sec = Math.floor((Date.now() - liveStartedAt) / 1000);
    $("liveClock").textContent = `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}`;
  }, 1000);
}
async function ensureLiveSession() {
  if (liveSessionId) return liveSessionId;
  const d = await api("/live/sessions", { method: "POST", json: { site_context: $("liveCtx").value.trim() } });
  liveSessionId = d.session_id; liveAlerts = []; liveFrames = 0;
  startClock();
  toast(T().liveStarted, "info");
  paintLive(); paintResumeRow(true);
  return liveSessionId;
}
$("liveStart").addEventListener("click", () => ensureLiveSession().catch((e) => toast(e.message, "err")));
$("resumeBtn").addEventListener("click", () => {
  const id = $("resumeSel").value;
  if (!id) return;
  liveSessionId = id; liveAlerts = []; liveFrames = 0;
  startClock(); paintLive(); paintResumeRow(true);
});
function onFrames(d) {
  liveFrames = d.frames_received;
  const now = Date.now();
  for (const a of d.new_alerts || []) {
    liveAlerts.push(Object.assign({ _at: now }, a));
    toast(lang === "ar" ? a.message_ar : a.message_en, "err");
    const st = $("stage"); st.classList.remove("flash"); void st.offsetWidth; st.classList.add("flash");
  }
  paintLive();
}
async function sendFrames(form) {
  try { onFrames(await api(`/live/sessions/${liveSessionId}/frames`, { method: "POST", form })); }
  catch (e) { if (e.status !== 401) toast(e.message, "err"); }
}
$("liveFileBtn").addEventListener("click", () => $("liveFiles").click());
$("liveFiles").addEventListener("change", async (e) => {
  if (!liveSessionId || !e.target.files.length) return;
  const fd = new FormData();
  for (const f of e.target.files) fd.append("files", f);
  e.target.value = "";
  await sendFrames(fd);
});
function stopCamera() {
  clearInterval(camTimer); camTimer = null;
  if (camStream) { camStream.getTracks().forEach((t) => t.stop()); camStream = null; }
  const v = $("camPreview"); v.srcObject = null; v.classList.add("hidden");
  paintLive();
}
function captureSnapshot() {
  const v = $("camPreview");
  if (!v.videoWidth || !liveSessionId) return;
  const c = document.createElement("canvas");
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext("2d").drawImage(v, 0, 0);
  c.toBlob((blob) => {
    if (!blob || !liveSessionId) return;
    const fd = new FormData();
    fd.append("files", blob, "camera-frame.jpg");
    sendFrames(fd);
  }, "image/jpeg", 0.85);
}
$("liveCam").addEventListener("click", async () => {
  const s = T();
  if (camStream) { stopCamera(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { toast(s.camDenied, "err"); return; }
  try {
    await ensureLiveSession();
    camStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const v = $("camPreview");
    v.srcObject = camStream; await v.play(); v.classList.remove("hidden");
    toast(s.camOn, "info");
    camTimer = setInterval(captureSnapshot, 3000);
    paintLive();
  } catch (e) { stopCamera(); toast(s.camDenied, "err"); }
});
$("liveFinish").addEventListener("click", async () => {
  if (!liveSessionId) return;
  stopCamera();
  const btn = $("liveFinish"); btn.disabled = true;
  $("liveStatus").textContent = T().finishing;
  try {
    const rep = await api(`/live/sessions/${liveSessionId}/finish`, { method: "POST", json: { notes: $("notes").value } });
    liveSessionId = null; clearInterval(liveClockTimer);
    report = rep;
    refreshSites(); refreshBadges();
    toast(T().done);
    go("#/report/" + rep.inspection_id);
  } catch (e) { toast(e.message, "err"); }
  finally { btn.disabled = false; $("liveStatus").textContent = T().liveHint; paintLive(); }
});

/* ---------------------------------------------------- inspection history */
const histState = { q: "", site: "", severity: "" };
const loadHistoryDebounced = debounce(() => loadHistory(), 250);
$("histQ").addEventListener("input", (e) => { histState.q = e.target.value; loadHistoryDebounced(); });
$("histSite").addEventListener("change", (e) => { histState.site = e.target.value; loadHistory(); });
$("histSev").addEventListener("change", (e) => { histState.severity = e.target.value; loadHistory(); });
function histQuery() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(histState)) if (v) p.set(k, v);
  return p.toString();
}
$("histCsv").addEventListener("click", () => downloadFile("/inspections?format=csv&" + histQuery(), "baseer-inspections.csv"));
async function loadHistory(query) {
  if (query && query.get("q") !== null) { histState.q = query.get("q"); $("histQ").value = histState.q; }
  const s = T();
  $("histRows").innerHTML = `<tr><td colspan="7"><div class="skeleton"></div></td></tr>`;
  let rows = [];
  try { rows = (await api("/inspections?" + histQuery())).inspections; } catch (e) { toast(e.message, "err"); }
  $("histEmpty").classList.toggle("hidden", rows.length > 0);
  $("histRows").innerHTML = rows.map((r) => {
    const total = r.open_cases + r.closed_cases;
    return `<tr data-href="#/report/${esc(r.inspection_id)}">
      <td><b class="mono">${esc(r.inspection_id)}</b><span class="cell-sub">${esc(pick(r, "top_finding"))}</span></td>
      <td>${esc(fmtTime(r.created_at))}</td>
      <td>${esc(r.site)}</td>
      <td><span class="badge badge-soft">${ic(r.source === "live-camera" ? "camera" : "upload")} ${esc(r.source === "live-camera" ? s.srcLive : s.srcUpload)}</span></td>
      <td><span class="mini-sev">${r.high ? `<span class="sev high">${r.high}</span>` : ""}${r.medium ? `<span class="sev medium">${r.medium}</span>` : ""}${r.low ? `<span class="sev low">${r.low}</span>` : ""}${!r.findings ? "—" : ""}</span></td>
      <td><div class="progress"><div class="track"><div class="fill" style="width:${total ? 100 * r.closed_cases / total : 0}%"></div></div><small>${esc(s.closedOf(r.closed_cases, total))}</small></div></td>
      <td class="chev">${ic("chevron")}</td></tr>`;
  }).join("");
}

/* ---------------------------------------------------------------- report */
let report = null;
const localMedia = new Map();   // inspection_id -> [{name, kind, url, size}] from this browser's upload
const serverMedia = new Map();  // inspection_id -> {name -> objectURL} fetched with auth
const chatHistories = new Map();
const EVIDENCE_VISIBLE = 12;
async function openReport(id, focus) {
  if (!id) {
    $("reportEmpty").classList.toggle("hidden", !!report);
    $("reportContent").classList.toggle("hidden", !report);
    if (report) { history.replaceState(null, "", "#/report/" + report.inspection_id); renderReport(); loadEvidence(report); }
    return;
  }
  if (!report || report.inspection_id !== id) {
    try { report = await api("/inspections/" + encodeURIComponent(id)); }
    catch (e) { report = null; toast(T().notFound, "err"); $("reportEmpty").classList.remove("hidden"); $("reportContent").classList.add("hidden"); return; }
  }
  $("reportEmpty").classList.add("hidden");
  $("reportContent").classList.remove("hidden");
  renderReport();
  if (focus !== null && focus !== undefined) {
    const el = $("finding-" + focus);
    if (el) { el.classList.add("focus"); el.scrollIntoView({ behavior: "smooth", block: "start" }); setTimeout(() => el.classList.remove("focus"), 2600); }
  }
  loadEvidence(report);
}
function pipeBadge(r) {
  const s = T();
  if (r.mode !== "live") return { cls: "demo", text: s.pipeBadgeMock };
  if (r.segmentation_source === "sam") return { cls: "sam", text: s.pipeBadgeSam };
  return { cls: "vision", text: s.pipeBadgeVision };
}
function mediaFor(r) {
  const local = localMedia.get(r.inspection_id);
  if (local) return local;
  const cache = serverMedia.get(r.inspection_id) || {};
  return (r.evidence_files || []).map((name) => ({ name, kind: isVideo(name) ? "video" : "image", url: cache[name] || "", server: true }));
}
// Frame index -> image: extract_frames emits one frame per image in upload
// order, but a video emits several, so mapping stops at the first video.
function frameShots(r) {
  const shots = [];
  for (const m of mediaFor(r)) { if (m.kind === "video") break; shots.push(m); }
  return shots;
}
async function loadEvidence(r) {
  if (localMedia.has(r.inspection_id)) return;
  const cache = serverMedia.get(r.inspection_id) || {};
  serverMedia.set(r.inspection_id, cache);
  const want = (r.evidence_files || []).filter((n) => !isVideo(n) && !cache[n]).slice(0, EVIDENCE_VISIBLE);
  if (!want.length) return;
  await Promise.all(want.map(async (name) => {
    try {
      const res = await api(`/inspections/${r.inspection_id}/evidence/${encodeURIComponent(name)}`, { raw: true });
      cache[name] = URL.createObjectURL(await res.blob());
    } catch (e) { /* missing evidence renders as a placeholder */ }
  }));
  if (report && report.inspection_id === r.inspection_id) { renderEvidence(); renderFindings(); }
}
function renderReport() {
  const r = report, s = T();
  if (!r) return;
  const b = pipeBadge(r);
  $("pipeBadge").className = "badge " + b.cls; $("pipeBadge").textContent = b.text;
  $("srcBadge").textContent = r.source === "live-camera" ? s.srcLive : s.srcUpload;
  $("rId").textContent = r.inspection_id;
  $("rMeta").textContent = s.meta(r);
  const c = { high: 0, medium: 0, low: 0 };
  r.findings.forEach((f) => { c[f.severity] = (c[f.severity] || 0) + 1; });
  $("sevStrip").innerHTML = `<div><small>${esc(s.stripTotal)}</small><b>${r.findings.length}</b></div>` +
    ["high", "medium", "low"].map((k) => `<div><small>${esc(s.sev[k])}</small><b class="c-${k === "medium" ? "med" : k}">${c[k]}</b></div>`).join("");
  $("rSummary").textContent = lang === "ar" ? (r.summary_ar || r.summary_en) : (r.summary_en || r.summary_ar);
  $("findingsCount").textContent = s.findingsN(r.findings.length);
  renderEvidence();
  renderFindings();
  renderBriefing();
  renderChat();
}

/* ---- crew briefing (toolbox talk in the crew's language) */
const BRIEF_FALLBACK = { ar: ["Arabic", "العربية", true], en: ["English", "English", false], ur: ["Urdu", "اردو", true],
  hi: ["Hindi", "हिन्दी", false], bn: ["Bengali", "বাংলা", false], ne: ["Nepali", "नेपाली", false],
  tl: ["Tagalog", "Tagalog", false], ml: ["Malayalam", "മലയാളം", false] };
const SPEECH_LANG = { ar: "ar", en: "en", ur: "ur", hi: "hi", bn: "bn", ne: "ne", tl: "fil", ml: "ml" };
let briefLang = null, briefFor = null;
function briefLangs() {
  const h = health.briefing_languages;
  return h ? Object.fromEntries(Object.entries(h).map(([k, v]) => [k, [v.name, v.native, v.rtl]])) : BRIEF_FALLBACK;
}
function renderBriefing() {
  const r = report, s = T(), langs = briefLangs(), done = r.briefings || {};
  if (briefFor !== r.inspection_id) { briefFor = r.inspection_id; briefLang = null; }
  $("briefCard").classList.toggle("hidden", !r.findings.length);
  $("briefLangs").innerHTML = Object.entries(langs).map(([k, v]) =>
    `<button type="button" data-brief="${k}" class="${k === briefLang ? "active" : ""}" lang="${k}">${esc(v[1])}${done[k] ? '<span class="done"></span>' : ""}</button>`).join("");
  const entry = briefLang && done[briefLang];
  const out = $("briefOut");
  out.className = "brief-out";
  out.dir = briefLang && langs[briefLang] && langs[briefLang][2] ? "rtl" : "auto";
  out.lang = briefLang || "";
  out.textContent = entry ? entry.text : (briefLang ? "" : s.briefPick);
  $("briefActions").classList.toggle("hidden", !entry);
  $("briefMeta").textContent = entry ? `${entry.actor || ""} · ${fmtTime(entry.generated_at)}` : "";
}
async function makeBriefing(code, refresh = false) {
  if (!report) return;
  const id = report.inspection_id;
  briefLang = code;
  renderBriefing();
  if ((report.briefings || {})[code] && !refresh) return;
  const out = $("briefOut");
  out.className = "brief-out loading"; out.textContent = T().briefWorking;
  $("briefActions").classList.add("hidden");
  try {
    const d = await api(`/inspections/${id}/briefing`, { method: "POST", json: { language: code, refresh } });
    if (report && report.inspection_id === id) {
      report.briefings = report.briefings || {};
      report.briefings[code] = { text: d.text, generated_at: d.generated_at, actor: d.actor };
    }
  } catch (e) { toast(e.message, "err"); }
  if (report && report.inspection_id === id) renderBriefing();
}
$("briefLangs").addEventListener("click", (e) => { const b = e.target.closest("[data-brief]"); if (b) makeBriefing(b.dataset.brief); });
$("briefRedo").addEventListener("click", () => briefLang && makeBriefing(briefLang, true));
$("briefCopy").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("briefOut").textContent); toast(T().briefCopied); } catch (e) { toast(e.message, "err"); }
});
$("briefWa").addEventListener("click", () => {
  window.open("https://wa.me/?text=" + encodeURIComponent($("briefOut").textContent), "_blank", "noopener");
});
$("briefSpeak").addEventListener("click", () => {
  const code = SPEECH_LANG[briefLang] || briefLang, name = (briefLangs()[briefLang] || [briefLang])[0];
  const voice = ("speechSynthesis" in window) && speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(code));
  if (!voice) return toast(T().briefNoVoice(name), "info");
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance($("briefOut").textContent);
  u.voice = voice; u.lang = voice.lang; u.rate = 0.95;
  speechSynthesis.speak(u);
});
function renderEvidence() {
  const r = report, s = T(), media = mediaFor(r);
  $("evStamp").textContent = media.length ? `${media.length} · ${fmtTime(r.created_at)}` : "";
  if (!media.length) { $("rEvidence").innerHTML = `<p class="muted small">${esc(s.noEvidence)}</p>`; return; }
  const shown = media.slice(0, EVIDENCE_VISIBLE);
  const nSegs = samSegments(r).filter((sg) => (sg.bbox || []).length === 4).length;
  // Images before the first video map one-to-one onto extracted frames.
  const firstVideo = media.findIndex((m) => m.kind === "video");
  $("segToggle").classList.toggle("hidden", !nSegs);
  $("segToggleLabel").textContent = s.segToggle(r.segmentation_source, nSegs, showSegs);
  $("rEvidence").innerHTML = shown.map((m, i) => {
    let visual;
    const fi = m.kind === "image" && (firstVideo < 0 || i < firstVideo) ? i : -1, segs = fi >= 0 ? segsFor(r, fi) : [];
    if (m.kind === "video") visual = m.url ? `<video src="${m.url}" controls preload="metadata"></video>` : `<button type="button" class="icon-btn" data-play="${i}" title="${esc(s.loadVideo)}">${ic("play")}</button>`;
    else visual = m.url ? `<img src="${m.url}" alt="" data-zoom="${m.url}" data-frame="${fi}">` : `<div class="skeleton" style="width:60%"></div>`;
    if (segs.length && showSegs) visual += `<span class="seg-badge">SAM · ${segs.length}</span>`;
    return `<div class="ev"><div class="ev-media">${visual}</div><div class="ev-info"><b>${esc(m.name.replace(/^\d+-(\d+-)?/, ""))}</b>${m.size ? fmtSize(m.size) : esc(m.kind)}</div></div>`;
  }).join("") + (media.length > shown.length ? `<div class="ev more">${esc(s.more(media.length - shown.length))}</div>` : "");
}
function zoom(z) { const fi = +(z.dataset.frame ?? -1); return lightbox(z.dataset.zoom, report && fi >= 0 && showSegs ? segsFor(report, fi) : []); }
$("segToggle").addEventListener("click", () => { showSegs = !showSegs; store.set("baseer_segs", showSegs); renderEvidence(); renderFindings(); });
$("rEvidence").addEventListener("click", async (e) => {
  const z = e.target.closest("[data-zoom]"); if (z) return zoom(z);
  const p = e.target.closest("[data-play]"); if (!p || !report) return;
  const m = mediaFor(report)[+p.dataset.play];
  try {
    const res = await api(`/inspections/${report.inspection_id}/evidence/${encodeURIComponent(m.name)}`, { raw: true });
    serverMedia.get(report.inspection_id)[m.name] = URL.createObjectURL(await res.blob());
    renderEvidence();
  } catch (ex) { toast(ex.message, "err"); }
});
function srcLabel(f) { const s = T(); return f.source === "inspector" ? s.srcInsp : f.source === "both" ? s.srcBoth : s.srcSeg; }
function deadline(f) {
  const days = (health.sla_days || {})[f.severity] ?? 30;
  const due = new Date(new Date(report.created_at).getTime() + days * 864e5);
  const status = (f.case || {}).status || "open";
  return { due, overdue: status !== "closed" && Date.now() > due.getTime() };
}
function dueLabel(c) {
  const s = T();
  if (!c.due_at) return "";
  const days = Math.round((new Date(c.due_at).getTime() - Date.now()) / 864e5);
  if (c.status === "closed") return fmtDate(c.due_at);
  return c.overdue ? s.dueAgo(Math.max(1, -days)) : s.dueIn(days);
}
function renderFindings() {
  const r = report, s = T(), shots = frameShots(r);
  if (!r.findings.length) { $("rFindings").innerHTML = `<div class="card empty">${ic("check-shield")}<b>${esc(s.noFindings)}</b></div>`; return; }
  $("rFindings").innerHTML = r.findings.map((f, i) => {
    const shot = shots[f.frame_index];
    return `<article class="finding" id="finding-${i}">
      <div class="finding-body ${f.severity}${shot && shot.url ? "" : " no-thumb"}">
        <div>
          <div class="row gap wrap"><span class="num">#${i + 1}</span><span class="sev ${f.severity}">${esc(s.sev[f.severity] || f.severity)}</span>
            ${f.determination === "uncertain" ? `<span class="badge uncertain">${esc(s.detUncertain)}</span>` : ""}</div>
          <h3>${esc(pick(f, "title"))}</h3>
          <p class="detail">${esc(pick(f, "detail"))}</p>
          ${pick(f, "action") ? `<div class="action-box">${ic("wrench")}<div><b>${esc(s.action)}</b>${esc(pick(f, "action"))}</div></div>` : ""}
          <div class="fmeta"><span class="badge badge-soft">${ic("image")} ${esc(s.frame(f.frame_index))}</span><span class="badge badge-soft">${ic("sparkles")} ${esc(srcLabel(f))}</span></div>
        </div>
        ${shot && shot.url ? `<div class="frame" data-zoom="${shot.url}" data-frame="${f.frame_index}"><img src="${shot.url}" alt="">${showSegs ? `<div class="seg-layer">${segLayer(segsFor(r, f.frame_index))}</div>` : ""}</div>` : ""}
      </div>
      ${caseHTML(f, i)}
    </article>`;
  }).join("");
}
function caseHTML(f, i) {
  const s = T(), c = f.case || { status: "open", assignee: "", verification: null, history: [] };
  const closed = c.status === "closed";
  const verified = !!(c.verification && c.verification.suggested_resolved);
  const stage = closed ? 3 : verified ? 2 : c.status === "assigned" ? 1 : 0;
  const { due, overdue } = deadline(f);
  const stepper = s.steps.map((label, k) => {
    const cls = k < stage || (closed && k === 3) ? "done" : k === stage ? "current" : "";
    return (k ? `<span class="ln ${k <= stage ? "done" : ""}"></span>` : "") +
      `<span class="st ${cls}"><span class="dot">${cls === "done" ? ic("check") : ""}</span><span>${esc(label)}</span></span>`;
  }).join("");
  const vtxt = c.verification ? (lang === "ar" ? c.verification.note_ar : c.verification.note_en) || c.verification.note || "" : "";
  const events = [...(c.history || []).map((h) => ({ ...h, kind: "h" })), ...(c.notes || []).map((n) => ({ ...n, kind: "n" }))]
    .sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
  const timeline = events.map((ev) => ev.kind === "n"
    ? `<li class="note"><b>${esc(ev.actor)}</b><small>${esc(fmtTime(ev.ts))}</small><p>${esc(ev.text)}</p></li>`
    : `<li><b>${esc(s.act[ev.action] || ev.action)}</b> · ${esc(ev.detail || "")}<small>${esc(ev.actor)} · ${esc(fmtTime(ev.ts))}</small></li>`).join("");
  const dis = closed ? "disabled" : "";
  return `<div class="case">
    <div class="case-top">
      <span class="case-title">${ic("clipboard")} ${esc(s.caseT)}
        <span class="status ${overdue ? "overdue" : c.status}">${esc(overdue ? s.overdue : s.status[c.status] || c.status)}</span>
        ${c.assignee ? `<span class="muted small">→ ${esc(c.assignee)}</span>` : ""}</span>
      <span class="small ${overdue ? "c-high" : "muted"}">${ic("clock")} ${esc(s.due(fmtTime(due.toISOString())))}</span>
    </div>
    <div class="stepper">${stepper}</div>
    ${closed ? "" : `<div class="case-actions">
      <input type="text" id="asg-${i}" list="assigneeList" placeholder="${esc(s.assignPh)}" value="${esc(c.assignee || "")}" ${dis}>
      <button type="button" class="btn btn-ghost btn-sm" data-case="assign" data-i="${i}">${ic("user")} ${esc(s.assign)}</button>
      <button type="button" class="btn btn-ghost btn-sm" data-case="verify" data-i="${i}">${ic("sparkles")} ${esc(s.verify)}</button>
      <button type="button" class="btn btn-ghost btn-sm" data-case="evidence" data-i="${i}">${ic("upload")} ${esc(s.verPhoto)}</button>
      <input type="file" id="ver-${i}" accept="image/*,video/*" hidden data-verify-file="${i}">
      <button type="button" class="btn btn-sm ${verified ? "btn-accent" : "btn-ghost"}" data-case="approve" data-i="${i}" ${verified ? "" : "disabled"}>${ic("check-shield")} ${esc(s.approve)}</button>
    </div>`}
    ${vtxt ? `<div class="verify-note ${verified ? "ok" : ""}">${esc(vtxt)}</div>` : ""}
    ${events.length ? `<details class="activity"${(c.notes || []).length ? " open" : ""}><summary>${esc(s.activity(events.length))}</summary>
      <ul class="timeline">${timeline}</ul></details>` : ""}
    <form class="note-form" data-note="${i}"><input type="text" maxlength="2000" placeholder="${esc(s.notePh)}"><button class="btn btn-ghost btn-sm" type="submit">${ic("message")} ${esc(s.noteAdd)}</button></form>
  </div>`;
}
function paintAssigneeList() {
  let dl = $("assigneeList");
  if (!dl) { dl = document.createElement("datalist"); dl.id = "assigneeList"; document.body.appendChild(dl); }
  dl.innerHTML = T().roles.map((r) => `<option value="${esc(r)}">`).join("");
}
async function caseUpdate(i, promise, okMsg) {
  try {
    report.findings[i] = await promise;
    toast(okMsg);
    renderFindings(); refreshBadges();
    const el = $("finding-" + i); if (el) el.querySelector("details.activity")?.setAttribute("open", "");
  } catch (e) { toast(e.message, "err"); }
}
$("rFindings").addEventListener("click", async (e) => {
  const z = e.target.closest("[data-zoom]"); if (z) return zoom(z);
  const b = e.target.closest("[data-case]"); if (!b || !report) return;
  const i = +b.dataset.i, s = T(), base = `/inspections/${report.inspection_id}/findings/${i}`;
  const action = b.dataset.case;
  if (action === "evidence") return $("ver-" + i).click();
  if (action === "assign") {
    const who = $("asg-" + i).value.trim();
    if (!who) return $("asg-" + i).focus();
    return caseUpdate(i, api(base + "/case", { method: "POST", json: { action: "assign", assignee: who } }), s.assigned);
  }
  if (action === "approve" && !(await modal({ title: s.approveQ, body: s.approveBody, ok: s.approve }))) return;
  b.disabled = true;
  await caseUpdate(i, api(base + "/case", { method: "POST", json: { action } }), action === "approve" ? s.closed : s.verified);
});
$("rFindings").addEventListener("change", (e) => {
  const inp = e.target.closest("[data-verify-file]");
  if (!inp || !inp.files.length || !report) return;
  const i = +inp.dataset.verifyFile, fd = new FormData();
  for (const f of inp.files) fd.append("files", f);
  caseUpdate(i, api(`/inspections/${report.inspection_id}/findings/${i}/verify-evidence`, { method: "POST", form: fd }), T().verified);
});
$("rFindings").addEventListener("submit", (e) => {
  const f = e.target.closest("[data-note]");
  if (!f || !report) return;
  e.preventDefault();
  const inp = f.querySelector("input"), text = inp.value.trim(), i = +f.dataset.note;
  if (!text) return;
  caseUpdate(i, api(`/inspections/${report.inspection_id}/findings/${i}/case/notes`, { method: "POST", json: { text } }), T().noteSaved);
});
$("pdfBtn").addEventListener("click", () => report && downloadFile(`/inspections/${report.inspection_id}/report.pdf`, `baseer-${report.inspection_id}.pdf`));
$("printBtn").addEventListener("click", () => window.print());
$("waBtn").addEventListener("click", () => {
  if (!report) return;
  const s = T();
  const lines = [`Baseer · ${report.inspection_id}`, $("rSummary").textContent, ""];
  report.findings.forEach((f, i) => { lines.push(`${i + 1}. [${s.sev[f.severity] || f.severity}] ${pick(f, "title")}`, `   ${s.action}: ${pick(f, "action")}`); });
  window.open("https://wa.me/?text=" + encodeURIComponent(lines.join("\n")), "_blank", "noopener");
});
$("copyLinkBtn").addEventListener("click", async () => {
  if (!report) return;
  const url = `${location.origin}${location.pathname}#/report/${report.inspection_id}`;
  try { await navigator.clipboard.writeText(url); toast(T().linkCopied); } catch (e) { toast(url, "info"); }
});

/* ---- evidence chat */
function renderChat() {
  const s = T(), hist = chatHistories.get(report.inspection_id) || [];
  $("chatChips").innerHTML = s.chips(report.findings[0]).map((c) => `<button type="button">${esc(c)}</button>`).join("");
  $("chatLog").innerHTML = hist.map((m) => `<div class="msg ${m.role === "user" ? "user" : "bot"}">${esc(m.content)}</div>`).join("");
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
}
$("chatChips").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) askChat(b.textContent); });
$("chatForm").addEventListener("submit", (e) => { e.preventDefault(); askChat($("chatInput").value); });
async function askChat(q) {
  q = (q || "").trim();
  if (!q || !report) return;
  const id = report.inspection_id, hist = chatHistories.get(id) || [];
  chatHistories.set(id, hist);
  $("chatInput").value = "";
  const log = $("chatLog");
  log.insertAdjacentHTML("beforeend", `<div class="msg user">${esc(q)}</div><div class="msg bot typing" id="typing"><span></span><span></span><span></span></div>`);
  log.scrollTop = log.scrollHeight;
  try {
    const d = await api(`/inspections/${id}/chat`, { method: "POST", json: { question: q, history: hist } });
    hist.push({ role: "user", content: q }, { role: "assistant", content: d.answer });
  } catch (e) { hist.push({ role: "user", content: q }, { role: "assistant", content: T().chatErr }); }
  if (report && report.inspection_id === id) renderChat();
}

/* ----------------------------------------------------------------- cases */
const caseState = { status: "", site: "", all: [] };
$("caseSite").addEventListener("change", (e) => { caseState.site = e.target.value; loadCases(caseState.status); });
$("casesCsv").addEventListener("click", () => downloadFile(`/cases?format=csv&status=${caseState.status}&site=${encodeURIComponent(caseState.site)}`, "baseer-cases.csv"));
async function loadCases(status) {
  caseState.status = status || "";
  $("caseRows").innerHTML = `<tr><td colspan="6"><div class="skeleton"></div></td></tr>`;
  try { caseState.all = (await api("/cases" + (caseState.site ? "?site=" + encodeURIComponent(caseState.site) : ""))).cases; }
  catch (e) { caseState.all = []; toast(e.message, "err"); }
  paintCases();
}
function paintCases() {
  const s = T(), all = caseState.all;
  const counts = { all: all.length, open: 0, assigned: 0, overdue: 0, closed: 0 };
  all.forEach((c) => { counts[c.status]++; if (c.overdue) counts.overdue++; });
  $("caseTabs").innerHTML = Object.keys(counts).map((k) =>
    `<button type="button" role="tab" data-tab="${k === "all" ? "" : k}" class="${(caseState.status || "") === (k === "all" ? "" : k) ? "active" : ""}">${esc(s.tabs[k])}<span>${counts[k]}</span></button>`).join("");
  const rows = all.filter((c) => !caseState.status || (caseState.status === "overdue" ? c.overdue : c.status === caseState.status));
  $("casesEmpty").classList.toggle("hidden", rows.length > 0);
  $("caseRows").innerHTML = rows.map((c) => `<tr data-href="#/report/${esc(c.inspection_id)}?f=${c.finding_index}">
    <td><b>${esc(pick(c, "title"))}</b><span class="cell-sub"><span class="mono">${esc(c.inspection_id)}</span> · #${c.finding_index + 1}${c.notes ? ` · ${ic("message")} ${c.notes}` : ""}</span></td>
    <td><span class="sev ${c.severity}">${esc(s.sev[c.severity])}</span></td>
    <td><span class="status ${c.overdue ? "overdue" : c.status}">${esc(c.overdue ? s.status.overdue : s.status[c.status])}</span>${c.suggested_resolved && c.status !== "closed" ? ` ${ic("check")}` : ""}</td>
    <td>${esc(c.assignee || "—")}</td>
    <td class="${c.overdue ? "c-high" : ""}">${esc(dueLabel(c))}<span class="cell-sub">${esc(fmtDate(c.due_at))}</span></td>
    <td>${esc(c.site)}</td></tr>`).join("");
}
$("caseTabs").addEventListener("click", (e) => {
  const b = e.target.closest("[data-tab]"); if (!b) return;
  caseState.status = b.dataset.tab;
  history.replaceState(null, "", "#/cases" + (caseState.status ? "?status=" + caseState.status : ""));
  paintCases();
});

/* ----------------------------------------------------------------- audit */
const auditState = { q: "", action: "", entries: [] };
$("auditQ").addEventListener("input", debounce((e) => { auditState.q = e.target.value.toLowerCase(); paintAudit(); }, 150));
$("auditAction").addEventListener("change", (e) => { auditState.action = e.target.value; paintAudit(); });
$("csvBtn").addEventListener("click", () => downloadFile("/audit?format=csv", "baseer-audit.csv"));
async function loadAudit() {
  try { auditState.entries = (await api("/audit")).entries; } catch (e) { auditState.entries = []; }
  paintAudit();
}
function paintAudit() {
  const s = T();
  const rows = auditState.entries.filter((e) => (!auditState.action || e.action === auditState.action) &&
    (!auditState.q || [e.inspection_id, e.site, e.actor, e.detail, e.finding].join(" ").toLowerCase().includes(auditState.q)));
  $("auditEmpty").classList.toggle("hidden", rows.length > 0);
  $("auditRows").innerHTML = rows.map((e) => `<tr>
    <td class="muted" style="white-space:nowrap">${esc(fmtTime(e.ts))}</td>
    <td><a class="mono link" href="#/report/${esc(e.inspection_id)}?f=${e.finding_index}">${esc(e.inspection_id)}</a></td>
    <td>${esc(e.site)}</td><td>#${e.finding_index + 1}<span class="cell-sub">${esc(e.finding)}</span></td>
    <td><span class="badge badge-soft">${esc(s.act[e.action] || e.action)}</span></td>
    <td>${esc(e.actor)}</td><td class="muted">${esc(e.detail)}</td></tr>`).join("");
}

/* ----------------------------------------------------------------- users */
async function loadUsers() {
  const s = T();
  let users = [];
  try { users = (await api("/auth/users")).users; } catch (e) { toast(e.message, "err"); }
  $("usersCount").textContent = s.usersN(users.length);
  $("userRows").innerHTML = users.map((u) => {
    const me = session && u.username === session.username;
    return `<tr>
      <td><div class="row gap"><span class="avatar">${esc(u.username.slice(0, 2))}</span><b>${esc(u.username)}</b>${me ? ` <span class="badge badge-soft">${esc(s.you)}</span>` : ""}</div></td>
      <td><select data-role="${esc(u.username)}" ${me ? "disabled" : ""}>${ROLE_KEYS.map((r) => `<option value="${r}"${r === u.role ? " selected" : ""}>${esc(roleName(r))}</option>`).join("")}</select></td>
      <td class="muted">${esc(fmtTime(u.created_at))}</td>
      <td><div class="row gap end">
        <button type="button" class="icon-btn" data-reset="${esc(u.username)}" title="${esc(s.resetPw)}">${ic("key")}</button>
        ${me ? "" : `<button type="button" class="icon-btn" data-del="${esc(u.username)}" title="${esc(s.delUser)}">${ic("trash")}</button>`}
      </div></td></tr>`;
  }).join("");
}
$("userRows").addEventListener("change", async (e) => {
  const sel = e.target.closest("[data-role]"); if (!sel) return;
  try { await api("/auth/users/" + encodeURIComponent(sel.dataset.role), { method: "PATCH", json: { role: sel.value } }); toast(T().roleSaved); }
  catch (ex) { toast(ex.message, "err"); loadUsers(); }
});
$("userRows").addEventListener("click", async (e) => {
  const s = T();
  const r = e.target.closest("[data-reset]");
  if (r) {
    const pw = await modal({ title: s.resetQ(r.dataset.reset), body: s.resetBody, ok: s.resetPw, input: true });
    if (!pw) return;
    try { await api("/auth/users/" + encodeURIComponent(r.dataset.reset), { method: "PATCH", json: { password: pw } }); toast(s.pwReset); }
    catch (ex) { toast(ex.message, "err"); }
  }
  const d = e.target.closest("[data-del]");
  if (d) {
    if (!(await modal({ title: s.delQ(d.dataset.del), body: s.delBody, ok: s.delUser, danger: true }))) return;
    try { await api("/auth/users/" + encodeURIComponent(d.dataset.del), { method: "DELETE" }); toast(s.userDeleted); loadUsers(); }
    catch (ex) { toast(ex.message, "err"); }
  }
});
$("newUserForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("nuErr");
  err.classList.add("hidden");
  try {
    await api("/auth/users", { method: "POST", json: { username: $("nuName").value.trim(), password: $("nuPass").value, role: $("nuRole").value } });
    $("nuName").value = ""; $("nuPass").value = "";
    toast(T().userAdded); loadUsers();
  } catch (ex) { err.textContent = ex.message; err.classList.remove("hidden"); }
});

/* --------------------------------------------------------------- account */
$("pwForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/auth/password", { method: "POST", json: { old_password: $("pwOld").value, new_password: $("pwNew").value } });
    toast(T().pwOk); $("pwOld").value = ""; $("pwNew").value = "";
  } catch (ex) { toast(ex.status === 400 ? ex.message : T().pwErr, "err"); }
});

/* ------------------------------------------------------------------- boot */
async function boot() {
  paintIcons();
  paintThemeButtons();
  paintAssigneeList();
  await loadHealth();
  applyLang();
  if (!session || !session.token) { paintUser(); booted = true; return; }
  try {
    const me = await api("/auth/me");
    session.username = me.username; session.role = me.role;
    store.set("baseer_session", session);
  } catch (e) {
    // Only a rejected token ends the session; a network blip keeps it.
    if (e.status === 401) { logout(); booted = true; return; }
  }
  paintUser();
  await refreshSites();
  refreshBadges();
  booted = true;
  renderRoute();
}
boot();
