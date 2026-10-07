"""
GTÜ Bilgisayar Mühendisliği 2026 OBS Birebir Müfredat Veritabanı
OBS ekranlarındaki resmi ders kodları (NonTElec3[0-1], FElec4[0-1], GenTelec8[0-1] vb.),
gerçek alt ders havuzları ve kredi/AKTS değerleri ile %100 uyumludur.
"""

# Sınıf bazlı zorunlu ve seçmeli ders planı (OBS'deki resmi kodlar ile)
CURRICULUM_SEMESTERS = {
    "1. Sınıf Dersleri": {
        "Güz (1. Yarıyıl)": [
            {"kod": "CSE101", "ad": "Introduction to Computer Engineering and Career Planning", "t": 3.5, "u": 0, "l": 0, "kredi": 3.5, "akts": 8, "tip": "Zorunlu"},
            {"kod": "CSE107", "ad": "Introduction to Computer Science Laboratory", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 2, "tip": "Zorunlu"},
            {"kod": "ENG151", "ad": "Science and Technology", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "HIS101", "ad": "Principles of Atatürk and the History of Turkish Revolution I", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "MATH101", "ad": "Calculus I", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 7, "tip": "Zorunlu"},
            {"kod": "PHYS121", "ad": "Physics I", "t": 4, "u": 0, "l": 0, "kredi": 4, "akts": 6, "tip": "Zorunlu"},
            {"kod": "PHYS151", "ad": "Physics Laboratory I", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 1, "tip": "Zorunlu"},
            {"kod": "TUR101", "ad": "Turkish I", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
        ],
        "Bahar (2. Yarıyıl)": [
            {"kod": "CSE102", "ad": "Computer Programming", "t": 4.5, "u": 0, "l": 0, "kredi": 4.5, "akts": 8, "tip": "Zorunlu"},
            {"kod": "CSE108", "ad": "Computer Programming Laboratory", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 2, "tip": "Zorunlu"},
            {"kod": "ENG152", "ad": "Culture of Science and Computation", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "HIS102", "ad": "Principles of Atatürk and The History of Turkish Revolution II", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "MATH102", "ad": "Calculus II", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 7, "tip": "Zorunlu"},
            {"kod": "PHYS122", "ad": "Physics II", "t": 4, "u": 0, "l": 0, "kredi": 4, "akts": 6, "tip": "Zorunlu"},
            {"kod": "PHYS152", "ad": "Physics Laboratory II", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 1, "tip": "Zorunlu"},
            {"kod": "TUR102", "ad": "Turkish II", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
        ]
    },
    "2. Sınıf Dersleri": {
        "Güz (3. Yarıyıl)": [
            {"kod": "CSE211", "ad": "Discrete Mathematics", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE231", "ad": "Circuits And Electronics", "t": 4, "u": 2, "l": 0, "kredi": 4, "akts": 8, "tip": "Zorunlu"},
            {"kod": "CSE233", "ad": "Circuits And Electronics Laboratory", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 2, "tip": "Zorunlu"},
            {"kod": "CSE241", "ad": "Object Oriented Programming", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 9, "tip": "Zorunlu"},
            {"kod": "ENGL111", "ad": "Business English", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "ENG401", "ad": "Occupational Health and Safety I", "t": 1, "u": 0, "l": 0, "kredi": 1, "akts": 1, "tip": "Zorunlu"},
            {"kod": "MATH118", "ad": "Probability and Statistics", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "NonTElec3[0-1]", "ad": "Nontechnical Elective I", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Non-Tech)"},
        ],
        "Bahar (4. Yarıyıl)": [
            {"kod": "CSE222", "ad": "Data Structures and Algorithms", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 9, "tip": "Zorunlu"},
            {"kod": "CSE232", "ad": "Logic Circuits And Design", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE234", "ad": "Logic Circuits And Design Laboratory", "t": 1, "u": 0, "l": 2, "kredi": 1, "akts": 2, "tip": "Zorunlu"},
            {"kod": "CSE344", "ad": "Systems Programming", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Zorunlu"},
            {"kod": "ENGL112", "ad": "Academic English", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 2, "tip": "Zorunlu"},
            {"kod": "ENG402", "ad": "Occupational Health and Safety II", "t": 1, "u": 0, "l": 0, "kredi": 1, "akts": 1, "tip": "Zorunlu"},
            {"kod": "MATH116", "ad": "Linear Algebra", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 6, "tip": "Zorunlu"},
            {"kod": "FElec4[0-1]", "ad": "Free Elective", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Free)"},
        ]
    },
    "3. Sınıf Dersleri": {
        "Güz (5. Yarıyıl)": [
            {"kod": "CSE321", "ad": "Introduction to Algorithm Design", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE331", "ad": "Computer Organization", "t": 4, "u": 0, "l": 0, "kredi": 4, "akts": 7, "tip": "Zorunlu"},
            {"kod": "CSE343", "ad": "Software Engineering", "t": 4, "u": 0, "l": 0, "kredi": 4, "akts": 8, "tip": "Zorunlu"},
            {"kod": "ENG300", "ad": "Summer Practice I", "t": 0.5, "u": 0, "l": 0, "kredi": 0.5, "akts": 1, "tip": "Staj"},
            {"kod": "MATH217", "ad": "Linear Algebra and Differential Equations", "t": 5, "u": 0, "l": 0, "kredi": 5, "akts": 8, "tip": "Zorunlu"},
            {"kod": "NonTElec5[0-1]", "ad": "Nontechnical Elective II", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Non-Tech)"},
        ],
        "Bahar (6. Yarıyıl)": [
            {"kod": "CSE312", "ad": "Operating Systems", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE341", "ad": "Programming Languages", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE351", "ad": "Signals and Systems", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Zorunlu"},
            {"kod": "CSE355", "ad": "Numerical Analysis in Computer Engineering", "t": 4, "u": 0, "l": 0, "kredi": 4, "akts": 8, "tip": "Zorunlu"},
            {"kod": "CSE396", "ad": "Computer Engineering Project", "t": 2, "u": 2, "l": 0, "kredi": 2, "akts": 5, "tip": "Zorunlu"},
            {"kod": "MultiElec6[0-1]", "ad": "Multidisciplinary Elective", "t": 1.5, "u": 0, "l": 0, "kredi": 1.5, "akts": 3, "tip": "Seçmeli (Çok Disiplinli)"},
            {"kod": "TElec6[0-1]", "ad": "Technical Elective", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Teknik)"},
        ]
    },
    "4. Sınıf Dersleri": {
        "Güz (7. Yarıyıl)": [
            {"kod": "CSE495", "ad": "Graduation Project I", "t": 1, "u": 0, "l": 0, "kredi": 1, "akts": 6, "tip": "Zorunlu"},
            {"kod": "DElec7[0-3]", "ad": "Departmental Elective I", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Seçmeli (Bölüm)"},
            {"kod": "GenTelec7[0-1]", "ad": "General Technical Elective I", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Gen-Tek)"},
        ],
        "Bahar (8. Yarıyıl)": [
            {"kod": "CSE496", "ad": "Graduation Project II", "t": 1, "u": 0, "l": 0, "kredi": 1, "akts": 6, "tip": "Zorunlu"},
            {"kod": "ENG400", "ad": "Summer Practice II", "t": 0.5, "u": 0, "l": 0, "kredi": 0.5, "akts": 1, "tip": "Staj"},
            {"kod": "ENG497", "ad": "Industry Oriented Research Project", "t": 1.5, "u": 0, "l": 0, "kredi": 1.5, "akts": 15, "tip": "Zorunlu"},
            {"kod": "DElec8[0-3]", "ad": "Departmental Elective II", "t": 3, "u": 0, "l": 0, "kredi": 3, "akts": 6, "tip": "Seçmeli (Bölüm)"},
            {"kod": "GenTelec8[0-1]", "ad": "General Technical Elective II", "t": 2, "u": 0, "l": 0, "kredi": 2, "akts": 3, "tip": "Seçmeli (Gen-Tek)"},
        ]
    }
}

# ==============================================================================
# SEÇMELİ ALT DERSLER HAVUZU (OBS'de Açılan Gerçek Alt Dersler)
# ==============================================================================

# NonTElec3[0-1], NonTElec5[0-1], FElec4[0-1], GenTelec7[0-1], GenTelec8[0-1] ortak havuzu
OBS_GENERAL_SUBCOURSES = [
    {"kod": "GTU110", "ad": "Scientific and Technological Activities", "kredi": 2, "akts": 3},
    {"kod": "GTU101", "ad": "Extracurricular Activities", "kredi": 1, "akts": 3},
    {"kod": "ENG250", "ad": "Economics", "kredi": 3, "akts": 3},
    {"kod": "ENG470", "ad": "Sustainability Literacy", "kredi": 2, "akts": 3},
    {"kod": "PES140", "ad": "Voluntary Work", "kredi": 2, "akts": 4},
    {"kod": "ENG450", "ad": "Health, Safety and Environment", "kredi": 2, "akts": 3},
    {"kod": "ENG362", "ad": "Algorithmic Diffusion of Innovations", "kredi": 2, "akts": 2},
    {"kod": "BUS403", "ad": "Business Skills and Career Management (BS)", "kredi": 4, "akts": 4},
    {"kod": "BUS441", "ad": "European Union: Institutions and Policy Making", "kredi": 3, "akts": 4},
    {"kod": "MATH419", "ad": "Introduction to Coding Theory", "kredi": 3, "akts": 6},
    {"kod": "BUS263", "ad": "Entrepreneurship", "kredi": 3, "akts": 4},
    {"kod": "ENG354", "ad": "Community Service Practices", "kredi": 2, "akts": 3},
    {"kod": "ENG353", "ad": "History of Science and Technology", "kredi": 2, "akts": 3},
    {"kod": "ENG313", "ad": "Narratives of Technology", "kredi": 2, "akts": 3},
]

# TElec6[0-1] (Teknik Seçmeli) Havuzu
OBS_TECHNICAL_SUBCOURSES = [
    {"kod": "GTU110", "ad": "Scientific and Technological Activities", "kredi": 2, "akts": 3},
    {"kod": "GTU101", "ad": "Extracurricular Activities", "kredi": 1, "akts": 3},
    {"kod": "BENG451", "ad": "Introduction to Bioinformatics", "kredi": 3, "akts": 6},
    {"kod": "ELEC334", "ad": "Microprocessors", "kredi": 3, "akts": 4},
    {"kod": "ENG250", "ad": "Economics", "kredi": 3, "akts": 3},
    {"kod": "PES140", "ad": "Voluntary Work", "kredi": 2, "akts": 4},
    {"kod": "ENVE315", "ad": "Energy and Environment", "kredi": 3, "akts": 5},
    {"kod": "ENG450", "ad": "Health, Safety and Environment", "kredi": 2, "akts": 3},
    {"kod": "MSE414", "ad": "Batteries and Fuel Cells", "kredi": 3, "akts": 5},
    {"kod": "BENG325", "ad": "Biomedical Engineering and Physiology", "kredi": 3, "akts": 5},
    {"kod": "BUS403", "ad": "Business Skills and Career Management (BS)", "kredi": 4, "akts": 4},
    {"kod": "IE101", "ad": "Introduction to Industrial Engineering and Career Planning", "kredi": 3, "akts": 5},
    {"kod": "BUS441", "ad": "European Union: Institutions and Policy Making", "kredi": 3, "akts": 4},
    {"kod": "MATH419", "ad": "Introduction to Coding Theory", "kredi": 3, "akts": 6},
    {"kod": "BUS263", "ad": "Entrepreneurship", "kredi": 3, "akts": 4},
    {"kod": "ENG354", "ad": "Community Service Practices", "kredi": 2, "akts": 3},
    {"kod": "ENG353", "ad": "History of Science and Technology", "kredi": 2, "akts": 3},
    {"kod": "BENG225", "ad": "Biochemistry", "kredi": 3, "akts": 6},
]

# DElec7[0-3] ve DElec8[0-3] (Bölüm Seçmeli - CSE 4XX) Havuzu
OBS_DEPARTMENTAL_SUBCOURSES = [
    {"kod": "CSE462", "ad": "Applied Augmented Reality and 3D User Interfaces", "kredi": 3, "akts": 6},
    {"kod": "CSE443", "ad": "Object Oriented Analysis and Design", "kredi": 3, "akts": 6},
    {"kod": "CSE464", "ad": "Digital Image Processing", "kredi": 3, "akts": 6},
    {"kod": "CSE426", "ad": "Introduction to Symbolic Computation", "kredi": 3, "akts": 6},
    {"kod": "CSE435", "ad": "Parallel and Distributed Systems", "kredi": 3, "akts": 6},
    {"kod": "CSE436", "ad": "Introduction to Integrated Circuits", "kredi": 3, "akts": 6},
    {"kod": "CSE454", "ad": "Data Mining", "kredi": 3, "akts": 6},
    {"kod": "CSE461", "ad": "Computer Graphics", "kredi": 3, "akts": 6},
    {"kod": "CSE484", "ad": "Introduction to Natural Language Processing", "kredi": 3, "akts": 6},
    {"kod": "CSE476", "ad": "Mobile Communication Networks", "kredi": 3, "akts": 6},
    {"kod": "CSE414", "ad": "Introduction to Database", "kredi": 3, "akts": 6},
    {"kod": "CSE421", "ad": "Analysis of Algorithms", "kredi": 3, "akts": 6},
    {"kod": "CSE422", "ad": "Theory of Computation", "kredi": 3, "akts": 6},
    {"kod": "CSE433", "ad": "Embedded Systems", "kredi": 3, "akts": 6},
    {"kod": "CSE441", "ad": "Network Protocols", "kredi": 3, "akts": 6},
    {"kod": "CSE455", "ad": "Machine Learning", "kredi": 3, "akts": 6},
    {"kod": "CSE470", "ad": "Introduction to Cryptography", "kredi": 3, "akts": 6},
    {"kod": "CSE473", "ad": "Network and Information Security", "kredi": 3, "akts": 6},
    {"kod": "CSE481", "ad": "Artificial Intelligence", "kredi": 3, "akts": 6},
]

# Slot Eşleştirme Haritası: OBS resmi kodları ve PDF adlarının her ikisini de destekler
ELECTIVE_SLOTS_MAP = {
    # Resmi OBS Kodları
    "NonTElec3[0-1]": OBS_GENERAL_SUBCOURSES,
    "FElec4[0-1]": OBS_GENERAL_SUBCOURSES,
    "NonTElec5[0-1]": OBS_GENERAL_SUBCOURSES,
    "MultiElec6[0-1]": OBS_TECHNICAL_SUBCOURSES,
    "TElec6[0-1]": OBS_TECHNICAL_SUBCOURSES,
    "DElec7[0-3]": OBS_DEPARTMENTAL_SUBCOURSES,
    "GenTelec7[0-1]": OBS_GENERAL_SUBCOURSES,
    "DElec8[0-3]": OBS_DEPARTMENTAL_SUBCOURSES,
    "GenTelec8[0-1]": OBS_GENERAL_SUBCOURSES,

    # Eski / PDF / Arayüz Takma Adları (Geriye Dönük Uyumluluk)
    "Non-Technical Elective I": OBS_GENERAL_SUBCOURSES,
    "Non-Technical Elective II": OBS_GENERAL_SUBCOURSES,
    "Free Elective": OBS_GENERAL_SUBCOURSES,
    "Technical Elective": OBS_TECHNICAL_SUBCOURSES,
    "Multidisciplinary Elective": OBS_TECHNICAL_SUBCOURSES,
    "Departmental Elective I": OBS_DEPARTMENTAL_SUBCOURSES,
    "Departmental Elective II": OBS_DEPARTMENTAL_SUBCOURSES,
    "General Technical Elective I": OBS_GENERAL_SUBCOURSES,
    "General Technical Elective II": OBS_GENERAL_SUBCOURSES,
    "GENTELEC8[0-1]": OBS_GENERAL_SUBCOURSES,
}

ELECTIVE_GROUPS = ELECTIVE_SLOTS_MAP


def get_all_courses_flat():
    """Arama ve listeleme için tüm derslerin düz listesini döner."""
    courses = []
    seen = set()

    for sinif, sem_dict in CURRICULUM_SEMESTERS.items():
        for sem_name, dersler in sem_dict.items():
            for d in dersler:
                key = d["kod"]
                if key not in seen:
                    seen.add(key)
                    courses.append({**d, "sinif": sinif, "donem": sem_name})

    for d in OBS_DEPARTMENTAL_SUBCOURSES:
        key = d["kod"]
        if key not in seen:
            seen.add(key)
            courses.append({**d, "sinif": "4. Sınıf Dersleri", "donem": "Bölüm Seçmeli Havuzu", "tip": "Bölüm Seçmeli"})

    for d in OBS_GENERAL_SUBCOURSES:
        key = d["kod"]
        if key not in seen:
            seen.add(key)
            courses.append({**d, "sinif": "2/3/4. Sınıf Dersleri", "donem": "Sosyal/Genel Seçmeli Havuzu", "tip": "Sosyal Seçmeli"})

    return courses
