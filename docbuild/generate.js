const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, TabStopType, TabStopPosition,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak,
} = require("docx");

const CONTENT_WIDTH = 9360;
const ACCENT = "2E5A9C";
const LIGHT = "D9E2F3";
const ZEBRA = "F2F5FB";

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] }); }
function h2(t) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }); }
function p(t, opts = {}) { return new Paragraph({ spacing: { after: 120, line: 276 }, children: [new TextRun({ text: t, ...opts })] }); }
function bullet(t) { return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun(t)] }); }

function headerCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA }, margins: cellMargins,
    shading: { fill: ACCENT, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF" })] })],
  });
}
function cell(content, width, fill) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA }, margins: cellMargins, verticalAlign: VerticalAlign.CENTER,
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ children: [new TextRun(String(content))] })],
  });
}
function table(colWidths, headerLabels, rows) {
  const headerRow = new TableRow({ tableHeader: true, children: headerLabels.map((l, i) => headerCell(l, colWidths[i])) });
  const bodyRows = rows.map((r, ri) => new TableRow({ children: r.map((c, ci) => cell(c, colWidths[ci], ri % 2 === 1 ? ZEBRA : undefined)) }));
  return new Table({ width: { size: CONTENT_WIDTH, type: WidthType.DXA }, columnWidths: colWidths, rows: [headerRow, ...bodyRows] });
}
function spacer() { return new Paragraph({ children: [new TextRun("")] }); }

// ---- muka depan ----------------------------------------------------------
const coverMeta = [
  ["Aplikasi", "Sistem Pendaftaran Event Selamat"],
  ["Framework", "Django 5.2 LTS (Python 3.11)"],
  ["Modul CRUD", "Pendaftaran Event"],
  ["Pautan Live", "https://django.zahar.my (melalui Cloudflare Tunnel)"],
  ["Pangkalan Data", "SQLite"],
  ["Tarikh", "Jun 2026"],
];

const cover = [
  new Paragraph({ spacing: { before: 2200 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Sistem Pendaftaran Event Selamat", bold: true, size: 54, color: ACCENT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Aplikasi Web Selamat Berasaskan Mikroservis", size: 28, color: "444444" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [new TextRun({ text: "dengan Amalan Pembangunan Patuh-OWASP", size: 28, color: "444444" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 } }, children: [] }),
  spacer(),
  new Table({
    width: { size: 7200, type: WidthType.DXA }, columnWidths: [2500, 4700], alignment: AlignmentType.CENTER,
    rows: coverMeta.map(([k, v]) => new TableRow({ children: [
      new TableCell({ borders, width: { size: 2500, type: WidthType.DXA }, margins: cellMargins,
        shading: { fill: LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: k, bold: true })] })] }),
      new TableCell({ borders, width: { size: 4700, type: WidthType.DXA }, margins: cellMargins,
        children: [new Paragraph({ children: [new TextRun(v)] })] }),
    ] })),
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---- isi kandungan -------------------------------------------------------
const toc = [
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Isi Kandungan", bold: true, size: 32, color: ACCENT })] }),
  new TableOfContents("Isi Kandungan", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---- kandungan -----------------------------------------------------------
const body = [];

body.push(h1("1. Pengenalan"));
body.push(p("Sistem Pendaftaran Event Selamat ialah aplikasi web yang membolehkan pengguna melihat dan mendaftar untuk event, manakala admin pula boleh menguruskan event tersebut sepenuhnya. Projek ini dibina untuk menunjukkan cara membangunkan aplikasi web yang selamat — setiap fungsi dilengkapi kawalan keselamatan mengikut OWASP Top 10, OWASP ASVS, amalan secure coding, dan checklist semakan kod (input validation, access control, output encoding, error handling dan logging)."));
body.push(p("Aplikasi ini dibina menggunakan framework Django 5.2 LTS dan berjalan atas HTTPS. Untuk tujuan demo, ia diterbitkan ke internet melalui Cloudflare Tunnel di https://django.zahar.my, sementara aplikasi sebenarnya berjalan secara lokal di komputer."));
body.push(h2("1.1 Objektif"));
body.push(p("Membina satu aplikasi web yang kecil tetapi lengkap dan selamat, yang dapat membuktikan setiap keperluan keselamatan dipenuhi. Pendekatannya ialah menggunakan framework dan library keselamatan yang sudah teruji, bukannya menulis kod sendiri yang lebih mudah ada kelemahan."));

body.push(h1("2. Apa Yang Sistem Ini Buat"));
body.push(p("Sistem ini disusun dalam beberapa modul utama:"));
body.push(table([2800, 6560], ["Modul", "Apa yang ia buat"], [
  ["Daftar & Log Masuk", "Pengguna boleh buka akaun, log masuk, log keluar, dan reset kata laluan yang terlupa melalui emel. Setiap akaun baru sentiasa jadi pengguna biasa."],
  ["Kawalan Akses Ikut Peranan", "Ada dua peranan — Admin dan Pengguna Biasa. Peranan inilah yang menentukan apa yang boleh dilihat dan dibuat oleh setiap orang."],
  ["Pengurusan Event (CRUD)", "Admin boleh cipta, edit, terbitkan, dan padam event — tajuk, penerangan, lokasi, masa mula/tamat, kapasiti, dan banner."],
  ["Pendaftaran Event", "Pengguna biasa lihat event yang diterbitkan, daftar untuk satu tempat (kapasiti dikawal, daftar berganda dihalang), lihat senarai pendaftaran, dan boleh batal."],
  ["Profil Pengguna", "Setiap pengguna boleh kemas kini profil sendiri dan muat naik gambar profil."],
  ["Audit Log", "Admin boleh lihat rekod log masuk, log masuk gagal, dan tindakan penting (cipta/edit/padam) dari satu halaman khas."],
]));
body.push(h2("2.1 Contoh Penggunaan"));
body.push(bullet("Admin log masuk, cipta event “Tech Conference 2026” dengan kapasiti 100 orang, muat naik banner, kemudian terbitkan."));
body.push(bullet("Pengguna biasa daftar akaun, log masuk, buka event itu, dan tekan Daftar. Sistem rekod tempahan dan kurangkan bilangan tempat yang masih kosong."));
body.push(bullet("Kemudian pengguna buka “My Registrations” dan batal — tempat itu kosong semula."));
body.push(bullet("Semua tindakan ini, termasuk log masuk, direkod dalam audit log yang hanya admin boleh baca."));

body.push(h1("3. Peranan Pengguna"));
body.push(table([2400, 6960], ["Peranan", "Apa yang boleh dibuat"], [
  ["Admin", "Urus event sepenuhnya (cipta, edit, padam, terbitkan); lihat audit log; akses Django admin site; serta semua yang pengguna biasa boleh buat."],
  ["Pengguna Biasa", "Lihat dan daftar event yang diterbitkan; urus dan batal pendaftaran sendiri; edit profil dan gambar sendiri. Tak boleh masuk mana-mana halaman admin (akan dapat ralat 403)."],
]));
body.push(p("Peranan disimpan sebagai satu medan pada akaun pengguna dan menjadi rujukan tunggal untuk semua keputusan akses. Pengguna tak boleh naikkan peranan sendiri — itu hanya boleh dibuat dari admin site yang dilindungi.", { italics: true }));

body.push(h1("4. Teknologi & Seni Bina"));
body.push(p("Projek ini dibahagikan kepada beberapa app Django yang berasingan: accounts (pengguna, peranan, pengesahan), events (CRUD event dan pendaftaran), audit (logging), dan core (template asas, halaman ralat, dan validator muat naik fail). Tetapan pula dibahagi kepada base / development / production supaya tahap keselamatan jelas dan senang disemak."));
body.push(table([2400, 2600, 4360], ["Bahagian", "Teknologi", "Kenapa digunakan"], [
  ["Framework", "Django 5.2 LTS", "Framework matang yang selamat secara default dan ada sokongan jangka panjang."],
  ["Pangkalan data", "SQLite", "Database tanpa konfigurasi; semua capaian guna Django ORM, tiada raw SQL."],
  ["Hashing kata laluan", "argon2-cffi (Argon2id)", "Algoritma hashing kata laluan yang disyorkan OWASP."],
  ["Pertahanan brute-force", "django-axes", "Kunci akaun selepas beberapa kali log masuk gagal dan rekod cubaan."],
  ["Header keselamatan", "django-csp", "Tambah Content-Security-Policy untuk menghalang XSS."],
  ["Konfigurasi", "django-environ", "Muat secret dari fail .env, bukan tulis dalam kod."],
  ["Fail statik", "WhiteNoise", "Hidang CSS/JS dengan selamat dalam production (DEBUG off)."],
  ["Pengesahan imej", "Pillow", "Pastikan fail yang dimuat naik betul-betul imej."],
  ["Imbasan dependency", "pip-audit", "Semak semua library untuk kelemahan yang diketahui."],
  ["Akses awam", "Cloudflare Tunnel", "Dedahkan aplikasi HTTPS lokal di django.zahar.my dengan sijil yang sah."],
]));

body.push(new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Ciri Keselamatan (Patuh OWASP)")] }));
body.push(p("Semua keperluan keselamatan wajib telah dilaksanakan. Jadual di bawah menunjukkan setiap keperluan dan cara ia dipenuhi dalam sistem."));
body.push(table([2400, 1100, 5860], ["Keperluan", "OWASP", "Cara ia dilaksanakan"], [
  ["Input Validation", "ASVS V5 / A03", "Regex whitelist untuk username dan tajuk event, validator built-in Django, dan parameter URL bertaip. Semua input disahkan di server, dan database dicapai guna ORM sahaja, jadi SQL injection terhalang."],
  ["Authentication & Session", "ASVS V2 / A07", "Log masuk selamat, peraturan kata laluan kuat (minimum 12 aksara + gabungan huruf, nombor, simbol), session timeout 15 minit bila tak aktif, perlindungan CSRF pada setiap borang, dan cookie session bertanda Secure + HttpOnly + SameSite."],
  ["Access Control", "ASVS V4 / A01", "Semakan peranan pada setiap halaman dan tindakan (peranan salah dapat 403). Pengguna hanya nampak dan boleh batal pendaftaran sendiri — pemilikan objek dikawal supaya tiada IDOR. Rekod guna ID jenis UUID yang tak boleh diteka."],
  ["Error Handling", "ASVS V7", "Mode debug dimatikan dalam production, jadi tiada stack trace bocor kepada pengguna. Halaman ralat khas dipaparkan untuk ralat 400, 403, 404 dan 500."],
  ["Sensitive Data", "ASVS V3 / A02", "Kata laluan di-hash guna Argon2id. Kredential dan token tak pernah ditulis dalam log. Semua trafik guna TLS/HTTPS."],
  ["File Upload Security", "-", "Fail disemak ikut extension dan kandungan imej sebenar (Pillow), dihadkan kepada 2 MB, disimpan di luar web root, dan dinamakan semula kepada UUID rawak."],
  ["Configuration Security", "A05", "Secret disimpan dalam fail .env dan tidak dimasukkan ke dalam repo. Debug dimatikan dalam production dan dependency sentiasa dikemas kini."],
  ["Logging & Monitoring", "ASVS V7 / A09", "Log masuk gagal, log masuk berjaya, dan tindakan cipta/edit/padam direkod dalam audit log yang hanya admin boleh lihat. Tiada data sensitif direkod."],
  ["Dependency Management", "A06", "Dependency dipin pada versi tertentu dan diimbas guna pip-audit, yang setakat ini tidak menjumpai sebarang kelemahan."],
  ["Output Encoding / XSS", "ASVS V5 / A03", "Auto-escaping template Django meng-encode semua output secara default; Content-Security-Policy pula jadi lapisan pertahanan kedua."],
]));

body.push(h1("6. Cara Guna Sistem"));
body.push(h2("6.1 Demo Live"));
body.push(p("Aplikasi boleh dicapai di https://django.zahar.my. Sambungannya dilindungi sijil sah daripada Cloudflare; di belakang tabir, tunnel menyalurkan trafik ke server Django yang berjalan lokal (HTTPS sahaja)."));
body.push(h2("6.2 Jalankan Secara Lokal"));
body.push(bullet("Buat virtual environment dan install requirements (pip install -r requirements.txt)."));
body.push(bullet("Salin .env.example ke .env, kemudian set secret key."));
body.push(bullet("Jalankan migration (python manage.py migrate)."));
body.push(bullet("Muat data demo (python manage.py seed)."));
body.push(bullet("Start server selamat (python manage.py runserver_plus --cert-file certs/localhost 127.0.0.1:8000)."));
body.push(h2("6.3 Akaun Demo"));
body.push(table([2200, 2600, 4560], ["Peranan", "Login", "Nota"], [
  ["Admin", "admin / Admin#Secure123", "Boleh urus event dan lihat audit log."],
  ["Pengguna Biasa", "user / User#Secure123", "Boleh daftar event dan urus tempahan sendiri."],
]));
body.push(p("Ini akaun demo sahaja dan patut ditukar sebelum digunakan untuk kegunaan sebenar.", { italics: true }));

body.push(h1("7. Pengujian & Pengesahan"));
body.push(p("Tingkah laku keselamatan sistem disokong oleh ujian automatik dan tooling standard:"));
body.push(bullet("26 ujian automatik lulus — meliputi semakan peranan (403), peraturan no-IDOR (404 bila cuba akses data orang lain), had kapasiti dan daftar berganda, escaping XSS, kekuatan kata laluan, audit log masuk, semakan muat naik fail, dan halaman ralat khas."));
body.push(bullet("pip-audit tidak menjumpai sebarang kelemahan dalam mana-mana dependency."));
body.push(bullet("Semakan deployment Django (manage.py check --deploy) tiada isu langsung pada tetapan production."));

body.push(h1("8. Kesimpulan"));
body.push(p("Sistem Pendaftaran Event Selamat ini berjaya menyediakan aplikasi pendaftaran event yang lengkap dan berfungsi, sambil memenuhi semua keperluan keselamatan wajib. Dengan menggabungkan reka bentuk Django yang selamat secara default dan beberapa library keselamatan yang dipilih dengan elok — hashing Argon2, kunci brute-force, Content-Security-Policy, konfigurasi berasaskan .env, dan imbasan dependency — projek ini menunjukkan amalan secure coding dari hujung ke hujung, bermula daripada input validation sehinggalah ke peringkat monitoring."));

const doc = new Document({
  creator: "Sistem Pendaftaran Event Selamat",
  title: "Sistem Pendaftaran Event Selamat",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: ACCENT, font: "Calibri" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, color: "333333", font: "Calibri" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [ { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] } ] },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: cover },
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 2 } },
        children: [new TextRun({ text: "Sistem Pendaftaran Event Selamat", size: 18, color: "888888" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: "Aplikasi Web Patuh OWASP", size: 18, color: "888888" }),
          new TextRun({ text: "\tMuka surat ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
          new TextRun({ text: " / ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: "888888" }),
        ] })] }) },
      children: [...toc, ...body],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("F:/Projek Coding/django/Sistem_Pendaftaran_Event_Selamat.docx", buffer);
  console.log("Dokumen Bahasa Melayu siap.");
});
