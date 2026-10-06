"""Afrikaans. Keys are the exact English source strings; keep {placeholders} identical. Native-speaker review welcome."""

STRINGS: dict[str, str] = {
    # Short bits glued onto other sentences
    " Chance of pregnancy is higher until it closes.": " Die kans op swangerskap is hoër totdat dit sluit.",
    " These are your best days to try.": " Dit is jou beste dae om te probeer.",
    "(+{n} more)": "(+{n} meer)",
    ", right on your average.": ", presies jou gemiddeld.",
    ", {n} days longer than your average of {avg}.": ", {n} dae langer as jou gemiddeld van {avg}.",
    ", {n} days shorter than your average of {avg}.": ", {n} dae korter as jou gemiddeld van {avg}.",
    "{n} day": "{n} dag",
    "{n} days": "{n} dae",
    "{n} days to go": "nog {n} dae",
    "{w}w {d}d": "{w}w {d}d",
    "{label} {when} matches your usual pattern.": "{label} {when} pas by jou gewone patroon.",
    "Day {n}": "Dag {n}",
    "Week {n}": "Week {n}",
    "Today": "Vandag",
    "Welcome": "Welkom",
    "to get predictions": "om voorspellings te kry",
    "Heads-up: {label}": "Kop op: {label}",
    "Most logged: {items}.": "Meeste aangeteken: {items}.",
    "It lasted {n} days": "Dit het {n} dae geduur",
    # Phases
    "during your period": "tydens jou maandstonde",
    "after your period": "ná jou maandstonde",
    "around ovulation": "rondom ovulasie",
    "before your period": "voor jou maandstonde",
    # Status / cycle
    "12 months without a period": "12 maande sonder 'n maandstonde",
    "Days since period": "Dae sedert maandstonde",
    "Due {date}": "Verwag {date}",
    "Due {date}.": "Verwag {date}.",
    "Due {date} · trimester {t}. Only about 1 in 20 babies arrive on the due date itself.": (
        "Verwag {date} · trimester {t}. Net sowat 1 uit 20 babas kom op die verwagte datum self."
    ),
    "Estimated ovulation day": "Beraamde ovulasiedag",
    "Fertile days hidden on hormonal birth control": "Vrugbare dae versteek op hormonale voorbehoeding",
    "Fertile window": "Vrugbare venster",
    "Fertile window starts": "Vrugbare venster begin",
    "High chance of getting pregnant": "Hoë kans om swanger te raak",
    "Medium chance of getting pregnant": "Matige kans om swanger te raak",
    "Low chance of getting pregnant": "Lae kans om swanger te raak",
    "Last cycle recap": "Opsomming van jou vorige siklus",
    "Log your last period to unlock predictions and personalised insights.": (
        "Teken jou laaste maandstonde aan om voorspellings en persoonlike insigte te ontsluit."
    ),
    "Log your period": "Teken jou maandstonde aan",
    "Log your period when it starts": "Teken jou maandstonde aan wanneer dit begin",
    "Long cycles": "Lang siklusse",
    "Long periods": "Lang maandstondes",
    "Short cycles": "Kort siklusse",
    "Variable cycle length": "Wisselende sikluslengte",
    "Longer gaps are common now": "Langer gapings is nou algemeen",
    "No period for {n} days": "Geen maandstonde vir {n} dae nie",
    "Ovulation": "Ovulasie",
    "Ovulation (estimated)": "Ovulasie (beraam)",
    "Period": "Maandstonde",
    "Period expected": "Maandstonde verwag",
    "Period in": "Maandstonde oor",
    "Period in {n} day": "Maandstonde oor {n} dag",
    "Period in {n} days": "Maandstonde oor {n} dae",
    "Period is late": "Maandstonde is laat",
    "Period late by": "Maandstonde laat met",
    "Period late by {days}": "Maandstonde laat met {days}",
    "Predicted period": "Voorspelde maandstonde",
    "Pregnant": "Swanger",
    "Your period started": "Jou maandstonde het begin",
    "Your period was {n} days.": "Jou maandstonde was {n} dae.",
    "Your average cycle is {avg} days across {n} tracked cycles.": (
        "Jou gemiddelde siklus is {avg} dae oor {n} aangetekende siklusse."
    ),
    "Your cycle length varied by {n} days recently, so predictions are less certain.": (
        "Jou sikluslengte het onlangs met {n} dae gewissel, so voorspellings is minder seker."
    ),
    "Your egg is likely released today.": "Jou eiersel word waarskynlik vandag vrygestel.",
    "Your egg is likely released today (confirmed by your temperature).": (
        "Jou eiersel word waarskynlik vandag vrygestel (bevestig deur jou temperatuur)."
    ),
    "Your fertile window opens today and lasts about 6 days.": "Jou vrugbare venster begin vandag en duur sowat 6 dae.",
    "Your period is a week or more late. If pregnancy is possible, a test can help; otherwise stress and lifestyle changes are common causes.": (
        "Jou maandstonde is 'n week of meer laat. As swangerskap moontlik is, kan 'n toets help; "
        "andersins is stres en leefstylveranderinge algemene oorsake."
    ),
    "A full year without a period usually marks menopause. Any bleeding from now on should be checked by a doctor.": (
        "'n Volle jaar sonder 'n maandstonde dui gewoonlik op menopouse. "
        "Enige bloeding van nou af moet deur 'n dokter nagegaan word."
    ),
    "Gaps of 60+ days are common in late perimenopause. You're {months} of the 12 months that usually mark menopause. Pregnancy is still possible until then.": (
        "Gapings van 60+ dae is algemeen in laat perimenopouse. Jy is {months} van die 12 maande "
        "wat gewoonlik menopouse aandui. Swangerskap is tot dan nog moontlik."
    ),
    "At least one recent period lasted more than 7 days. Consider checking in with a healthcare provider.": (
        "Ten minste een onlangse maandstonde het langer as 7 dae geduur. Oorweeg dit om 'n gesondheidswerker te raadpleeg."
    ),
    "Some of your recent cycles were longer than 35 days. Stress, travel and hormones can cause this; talk to a professional if it persists.": (
        "Sommige van jou onlangse siklusse was langer as 35 dae. Stres, reis en hormone kan dit veroorsaak; "
        "praat met 'n professionele persoon as dit aanhou."
    ),
    "Some of your recent cycles were shorter than 21 days. Worth mentioning to a healthcare provider if it keeps happening.": (
        "Sommige van jou onlangse siklusse was korter as 21 dae. Noem dit aan 'n gesondheidswerker as dit aanhou gebeur."
    ),
    "Stress, travel, illness or sleep changes can delay a period. If pregnancy is possible, a home test is reliable from the day your period was due.": (
        "Stres, reis, siekte of slaapveranderinge kan 'n maandstonde vertraag. As swangerskap moontlik is, "
        "is 'n tuistoets betroubaar vanaf die dag wat jou maandstonde verwag is."
    ),
    "This is the fertile window, the days when pregnancy is most likely.": (
        "Dit is die vrugbare venster, die dae wanneer swangerskap die waarskynlikste is."
    ),
    "Ovulation is estimated around today, the peak of the fertile window.": (
        "Ovulasie word rondom vandag beraam, die hoogtepunt van die vrugbare venster."
    ),
    "Ovulation is estimated for today. Some people notice mild one-sided pain or a small temperature rise afterwards.": (
        "Ovulasie word vir vandag beraam. Sommige mense merk ligte eensydige pyn of 'n klein temperatuurstyging daarna."
    ),
    "You're in your fertile window. Cervical fluid often becomes clearer and stretchier around now.": (
        "Jy is in jou vrugbare venster. Servikale vloeistof word omtrent nou dikwels helderder en rekbaarder."
    ),
    "Your body is shedding the uterine lining. Warmth, gentle movement and iron-rich foods can help with cramps and fatigue.": (
        "Jou liggaam stort die baarmoedervoering. Warmte, sagte beweging en ysterryke kos kan help met krampe en moegheid."
    ),
    "Estrogen is rising, which often brings more energy and a brighter mood — a good time for new projects and harder workouts.": (
        "Estrogeen styg, wat dikwels meer energie en 'n beter bui bring — 'n goeie tyd vir nuwe projekte en harder oefensessies."
    ),
    "Progesterone is higher now. It's common to feel more tired, bloated or crave comfort food before your period.": (
        "Progesteroon is nou hoër. Dit is algemeen om voor jou maandstonde moeër of opgeblaas te voel of na troos-kos te smag."
    ),
    "Day 1 of a new cycle. Rest if you need it and keep a heat pad handy.": (
        "Dag 1 van 'n nuwe siklus. Rus as jy moet en hou 'n warmkussing byderhand."
    ),
    "Good time to pack pads, tampons or your cup.": "Goeie tyd om doekies, tampons of jou koppie in te pak.",
    "Positive pregnancy test logged. If this is happy news, congratulations! Switch to pregnancy mode in Profile → Life stage.": (
        "Positiewe swangerskaptoets aangeteken. As dit goeie nuus is, baie geluk! "
        "Skakel oor na swangerskapmodus in Profiel → Lewensfase."
    ),
    # Pregnancy
    "Trimester {t} tip": "Trimester {t}-wenk",
    "Your baby is about the size of a {size}.": "Jou baba is omtrent so groot soos 'n {size}.",
    "Ask about the anatomy scan, usually around weeks 18 to 22.": "Vra oor die anatomiese skandering, gewoonlik rondom weke 18 tot 22.",
    "Book your first prenatal appointment if you haven't yet.": "Bespreek jou eerste voorgeboortelike afspraak as jy nog nie het nie.",
    "Get to know your baby's movement pattern and call your provider if it changes or slows.": (
        "Leer jou baba se bewegingspatroon ken en bel jou gesondheidswerker as dit verander of stadiger word."
    ),
    "Nausea? Small, frequent snacks and ginger often help. Seek care if you can't keep fluids down.": (
        "Naar? Klein, gereelde peuselhappies en gemmer help dikwels. Kry hulp as jy nie vloeistof kan inhou nie."
    ),
    "Pack a hospital bag and plan your route by week 36.": "Pak teen week 36 'n hospitaalsak en beplan jou roete.",
    "Severe headache, vision changes or sudden swelling need a call to your provider right away.": (
        "Erge hoofpyn, visieveranderinge of skielike swelling: bel dadelik jou gesondheidswerker."
    ),
    "Sleeping on your side gets more comfortable as your bump grows; a pillow between the knees helps.": (
        "Op jou sy slaap word gemakliker soos jou maag groei; 'n kussing tussen die knieë help."
    ),
    "Swelling, heartburn and poor sleep are common now. Smaller meals and elevating your feet help.": (
        "Swelling, sooibrand en swak slaap is nou algemeen. Kleiner maaltye en jou voete oplig help."
    ),
    "Take a daily prenatal vitamin with folic acid, ideally 400 mcg.": (
        "Neem daagliks 'n voorgeboortelike vitamien met foliensuur, verkieslik 400 mcg."
    ),
    "Tiredness is normal this trimester. Rest when you can.": "Moegheid is normaal hierdie trimester. Rus wanneer jy kan.",
    "You may start feeling movements between weeks 16 and 22.": "Jy kan tussen weke 16 en 22 bewegings begin voel.",
    # Baby sizes
    "poppy seed": "papawersaadjie",
    "sesame seed": "sesamsaadjie",
    "lentil": "lensie",
    "blueberry": "bloubessie",
    "raspberry": "framboos",
    "cherry": "kersie",
    "strawberry": "aarbei",
    "lime": "lemmetjie",
    "lemon": "suurlemoen",
    "plum": "pruim",
    "peach": "perske",
    "apple": "appel",
    "pear": "peer",
    "avocado": "avokado",
    "banana": "piesang",
    "carrot": "wortel",
    "bell pepper": "soetrissie",
    "mango": "mango",
    "grapefruit": "pomelo",
    "papaya": "papaja",
    "cantaloupe": "spanspek",
    "ear of corn": "mielie",
    "eggplant": "eiervrug",
    "cauliflower": "blomkool",
    "lettuce": "blaarslaai",
    "romaine lettuce": "cos-slaai",
    "cabbage": "kool",
    "coconut": "klapper",
    "leek": "prei",
    "rutabaga": "koolraap",
    "butternut squash": "botterskorsie",
    "large jicama": "groot jicama",
    "pineapple": "pynappel",
    "honeydew melon": "winterspanspek",
    "swiss chard": "snybeet",
    "mini watermelon": "klein waatlemoen",
    "small pumpkin": "klein pampoen",
    # Partner tips
    "Energy usually climbs this week. A good time for plans, dates and doing active things together.": (
        "Energie styg gewoonlik hierdie week. 'n Goeie tyd vir planne, afsprake en aktiewe dinge saam."
    ),
    "PMS can show up in this phase: tiredness, bloating or a shorter fuse. Extra patience and comfort food are appreciated.": (
        "PMS kan in hierdie fase opduik: moegheid, opgeblasenheid of 'n korter lont. Ekstra geduld en troos-kos word waardeer."
    ),
    "Period days can mean cramps and low energy. A hot water bottle, snacks and taking a chore off her plate go a long way.": (
        "Maandstondedae kan krampe en lae energie beteken. 'n Warmwatersak, peuselhappies en 'n taak van haar bord af help baie."
    ),
    "Pregnancy is hard work for the body. Help with meals, chores and appointments, and ask how she's feeling today.": (
        "Swangerskap is harde werk vir die liggaam. Help met etes, take en afsprake, en vra hoe sy vandag voel."
    ),
    # Tips
    "Tip for this phase": "Wenk vir hierdie fase",
    "A heating pad on your lower belly relaxes the uterine muscles and can ease cramps.": (
        "'n Warmkussing op jou onderbuik ontspan die baarmoederspiere en kan krampe verlig."
    ),
    "A soft, supportive bra and less salt/caffeine can ease tenderness.": (
        "'n Sagte, ondersteunende bra en minder sout/kafeïen kan teerheid verlig."
    ),
    "Be kind to yourself today. If low mood lasts for weeks, talk to someone you trust or a professional.": (
        "Wees vandag sag met jouself. As 'n lae bui weke lank duur, praat met iemand wat jy vertrou of 'n professionele persoon."
    ),
    "Cervical fluid often turns clear and stretchy (like egg white) near ovulation.": (
        "Servikale vloeistof word naby ovulasie dikwels helder en rekbaar (soos eierwit)."
    ),
    "Cravings are common before your period. Complex carbs and magnesium-rich foods (nuts, dark chocolate) can help.": (
        "Drange is algemeen voor jou maandstonde. Komplekse koolhidrate en magnesiumryke kos (neute, donker sjokolade) kan help."
    ),
    "Cutting back on salt and caffeine this week can reduce bloating and breast tenderness.": (
        "Minder sout en kafeïen hierdie week kan opgeblasenheid en teer borste verminder."
    ),
    "Gentle movement like walking or yoga can reduce cramps more than you'd expect.": (
        "Sagte beweging soos stap of joga kan krampe meer verlig as wat jy sou verwag."
    ),
    "Great time to try something new: motivation and stamina tend to be higher.": (
        "Goeie tyd om iets nuuts te probeer: motivering en uithouvermoë is gewoonlik hoër."
    ),
    "Heat on your lower back and gentle cat-cow stretches can help.": "Warmte op jou onderrug en sagte kat-koei-strekke kan help.",
    "Heat, gentle stretching and staying hydrated can take the edge off.": "Warmte, sagte strek en genoeg water kan dit versag.",
    "Hormonal breakouts often follow the cycle — be gentle and avoid over-scrubbing.": (
        "Hormonale puisies volg dikwels die siklus — wees sag en moenie te hard skrop nie."
    ),
    "Hormone dips can trigger headaches — water, regular meals and rest help.": (
        "Hormoondalings kan hoofpyn veroorsaak — water, gereelde etes en rus help."
    ),
    "Hormone shifts can shorten your fuse — a short walk or some quiet time helps.": (
        "Hormoonskommelinge kan jou lont korter maak — 'n kort stappie of bietjie stiltetyd help."
    ),
    "Iron-rich food and an earlier night can help your energy recover.": "Ysterryke kos en 'n vroeër slaaptyd kan jou energie help herstel.",
    "Less salt, more water and a short walk after meals can reduce bloating.": (
        "Minder sout, meer water en 'n kort stappie ná etes kan opgeblasenheid verminder."
    ),
    "Libido often rises around ovulation — that's estrogen and testosterone peaking.": (
        "Libido styg dikwels rondom ovulasie — dis estrogeen en testosteroon wat 'n hoogtepunt bereik."
    ),
    "Many people feel more energetic now. A good time for gentle exercise like walking or swimming.": (
        "Baie mense voel nou meer energiek. 'n Goeie tyd vir sagte oefening soos stap of swem."
    ),
    "Many people find focus and mood lift now. Plan demanding tasks for this stretch.": (
        "Baie mense se fokus en bui verbeter nou. Beplan veeleisende take vir hierdie tydperk."
    ),
    "Progesterone rises now and can make you sleepier — an earlier bedtime helps.": (
        "Progesteroon styg nou en kan jou slaperiger maak — 'n vroeër slaaptyd help."
    ),
    "Prostaglandins peak in the first days; anti-inflammatory painkillers work best taken early.": (
        "Prostaglandiene is die eerste dae op hul hoogste; anti-inflammatoriese pynpille werk die beste as jy dit vroeg neem."
    ),
    "Regular meals and sleep smooth out the hormonal rollercoaster a little.": (
        "Gereelde etes en slaap maak die hormonale wipplank 'n bietjie gladder."
    ),
    "Rising estrogen often means more energy — a good week for tougher workouts or new projects.": (
        "Stygende estrogeen beteken dikwels meer energie — 'n goeie week vir harder oefensessies of nuwe projekte."
    ),
    "Slow breathing (in 4, out 6) for a couple of minutes calms the nervous system.": (
        "Stadige asemhaling (in 4, uit 6) vir 'n paar minute kalmeer die senuweestelsel."
    ),
    "Small, bland meals and ginger tea can settle your stomach.": "Klein, sagte maaltye en gemmertee kan jou maag kalmeer.",
    "Some people feel a brief one-sided twinge (mittelschmerz) when they ovulate.": (
        "Sommige mense voel 'n kort eensydige steek (mittelschmerz) wanneer hulle ovuleer."
    ),
    "Sperm can survive up to 5 days, which is why the fertile window starts before ovulation.": (
        "Sperm kan tot 5 dae oorleef, daarom begin die vrugbare venster voor ovulasie."
    ),
    "Totally normal. Pair treats with protein or fibre to avoid energy crashes.": (
        "Heeltemal normaal. Eet lekkernye saam met proteïen of vesel om energie-insinkings te vermy."
    ),
    "Try a cooler room and no screens for the last hour before bed.": "Probeer 'n koeler kamer en geen skerms die laaste uur voor slaaptyd.",
    "You lose iron while bleeding — lentils, spinach, red meat or beans with vitamin C help replace it.": (
        "Jy verloor yster terwyl jy bloei — lensies, spinasie, rooivleis of boontjies met vitamien C help om dit te vervang."
    ),
    "Your body temperature is slightly higher now, so you may sleep better in a cooler room.": (
        "Jou liggaamstemperatuur is nou effens hoër, so jy slaap dalk beter in 'n koeler kamer."
    ),
    "Your skin often looks its best in this phase as estrogen rises.": "Jou vel lyk dikwels op sy beste in hierdie fase soos estrogeen styg.",
    # Catalog: categories
    "Symptoms": "Simptome",
    "Mood": "Bui",
    "Sex and sex drive": "Seks en seksdrang",
    "Vaginal discharge": "Vaginale afskeiding",
    "Digestion and stool": "Spysvertering en stoelgang",
    "Physical activity": "Fisieke aktiwiteit",
    "Oral contraceptives": "Orale voorbehoedmiddels",
    "Ovulation test": "Ovulasietoets",
    "Pregnancy test": "Swangerskaptoets",
    "Other": "Ander",
    # Catalog: flow
    "Spotting": "Vlekkies",
    "Light": "Lig",
    "Medium": "Medium",
    "Heavy": "Swaar",
    # Catalog: symptoms
    "Everything is fine": "Alles is reg",
    "Cramps": "Krampe",
    "Tender breasts": "Teer borste",
    "Headache": "Hoofpyn",
    "Acne": "Puisies",
    "Backache": "Rugpyn",
    "Fatigue": "Moegheid",
    "Cravings": "Drange",
    "Insomnia": "Slapeloosheid",
    "Abdominal pain": "Maagpyn",
    "Vaginal itching": "Vaginale jeuk",
    "Vaginal dryness": "Vaginale droogheid",
    "Bloating": "Opgeblasenheid",
    "Nausea": "Naarheid",
    "Dizziness": "Duiseligheid",
    "Hot flashes": "Warm gloede",
    "Night sweats": "Nagsweet",
    "Joint pain": "Gewrigspyn",
    "Brain fog": "Breinmis",
    "Palpitations": "Hartkloppings",
    # Catalog: mood
    "Calm": "Kalm",
    "Happy": "Gelukkig",
    "Energetic": "Energiek",
    "Frisky": "Speels",
    "Mood swings": "Buiwisselings",
    "Irritated": "Geïrriteerd",
    "Sad": "Hartseer",
    "Anxious": "Angstig",
    "Depressed": "Neerslagtig",
    "Feeling guilty": "Voel skuldig",
    "Obsessive thoughts": "Obsessiewe gedagtes",
    "Low energy": "Lae energie",
    "Apathetic": "Apaties",
    "Confused": "Deurmekaar",
    "Very self-critical": "Baie selfkrities",
    # Catalog: sex
    "Didn't have sex": "Nie seks gehad nie",
    "Protected sex": "Beskermde seks",
    "Unprotected sex": "Onbeskermde seks",
    "Oral sex": "Orale seks",
    "Anal sex": "Anale seks",
    "Masturbation": "Masturbasie",
    "Sensual touch": "Sensuele aanraking",
    "Sex toys": "Seksspeelgoed",
    "Orgasm": "Orgasme",
    "High sex drive": "Hoë seksdrang",
    "Neutral sex drive": "Gewone seksdrang",
    "Low sex drive": "Lae seksdrang",
    # Catalog: discharge
    "No discharge": "Geen afskeiding",
    "Creamy": "Romerig",
    "Watery": "Waterig",
    "Sticky": "Taai",
    "Egg white": "Eierwit",
    "Unusual": "Ongewoon",
    "Clumpy white": "Klonterig wit",
    "Gray": "Grys",
    # Catalog: digestion
    "Constipation": "Hardlywigheid",
    "Diarrhea": "Diarree",
    # Catalog: activity
    "Didn't exercise": "Nie geoefen nie",
    "Yoga": "Joga",
    "Gym": "Gimnasium",
    "Aerobics & dancing": "Aërobiese oefening en dans",
    "Swimming": "Swem",
    "Team sports": "Spansport",
    "Running": "Hardloop",
    "Cycling": "Fietsry",
    "Walking": "Stap",
    # Catalog: pill, tests, other
    "Taken on time": "Betyds geneem",
    "Missed pill": "Pil gemis",
    "Double dose": "Dubbele dosis",
    "Didn't take tests": "Nie getoets nie",
    "Test: positive": "Toets: positief",
    "Test: negative": "Toets: negatief",
    "Faint line": "Dowwe streep",
    "Travel": "Reis",
    "Stress": "Stres",
    "Meditation": "Meditasie",
    "Journaling": "Joernaal skryf",
    "Kegel exercises": "Kegel-oefeninge",
    "Breathing exercises": "Asemhalingsoefeninge",
    "Disease or injury": "Siekte of besering",
    "Alcohol": "Alkohol",
    # Birth control
    "Active pill {day} of {total}.": "Aktiewe pil {day} van {total}.",
    "After your period, gently check you can feel the strings.": "Ná jou maandstonde, voel saggies of jy die drade kan voel.",
    "Book a replacement by {date}.": "Bespreek 'n vervanging teen {date}.",
    "Book a replacement now.": "Bespreek nou 'n vervanging.",
    "Book or confirm your appointment.": "Bespreek of bevestig jou afspraak.",
    "Break day {n} of {total}": "Breekdag {n} van {total}",
    "Break starts in {n} days.": "Breek begin oor {n} dae.",
    "Change your patch today": "Vervang vandag jou pleister",
    "Due {n} days ago. Contact your clinic; you may need backup protection.": (
        "{n} dae gelede verwag. Kontak jou kliniek; jy het dalk ekstra beskerming nodig."
    ),
    "IUD in place": "Spiraal in plek",
    "IUD replacement due": "Spiraal moet vervang word",
    "Implant in place": "Inplanting in plek",
    "Implant replacement due": "Inplanting moet vervang word",
    "Injection due today": "Inspuiting vandag verwag",
    "Injection overdue": "Inspuiting is agterstallig",
    "Insert a new ring in {n} days.": "Plaas oor {n} dae 'n nuwe ring.",
    "Insert a new ring tomorrow": "Plaas môre 'n nuwe ring",
    "It has been in for 3 weeks tomorrow.": "Dit is môre 3 weke in.",
    "Monthly IUD string check": "Maandelikse spiraaldraadtoets",
    "New patch in {n} days.": "Nuwe pleister oor {n} dae.",
    "New patch tomorrow": "Nuwe pleister môre",
    "Next change in {n} days.": "Volgende vervanging oor {n} dae.",
    "Next injection in {n} days": "Volgende inspuiting oor {n} dae",
    "No replacement date set.": "Geen vervangingsdatum gestel nie.",
    "Patch {n} of 3": "Pleister {n} van 3",
    "Patch {n} of 3 this cycle.": "Pleister {n} van 3 hierdie siklus.",
    "Patch-free day {n}": "Pleistervrye dag {n}",
    "Patch-free week; new patch in 7 days.": "Pleistervrye week; nuwe pleister oor 7 dae.",
    "Pill day {n}": "Pildag {n}",
    "Pill reminder": "Pilherinnering",
    "Progestin-only pill: same time every day, no break.": "Progestien-alleen-pil: elke dag dieselfde tyd, geen breek nie.",
    "Remove it in {n} days.": "Haal dit oor {n} dae uit.",
    "Remove your ring today": "Haal vandag jou ring uit",
    "Remove your ring tomorrow": "Haal môre jou ring uit",
    "Replace by {date}.": "Vervang teen {date}.",
    "Ring week {n}": "Ringweek {n}",
    "Ring-free day {n}": "Ringvrye dag {n}",
    "Ring-free week until a new ring in 7 days.": "Ringvrye week tot 'n nuwe ring oor 7 dae.",
    "Start a new pack tomorrow.": "Begin môre 'n nuwe pakkie.",
    "Start your next pack on {date}.": "Begin jou volgende pakkie op {date}.",
    "Take your patch off today": "Haal vandag jou pleister af",
    "Take your pill": "Neem jou pil",
    "Time to take your pill.": "Tyd om jou pil te neem.",
    "Your patch-free week ends tomorrow.": "Jou pleistervrye week eindig môre.",
    "Your ring-free week ends tomorrow.": "Jou ringvrye week eindig môre.",
    # Notifications, log, report
    "About today's log": "Oor vandag se aantekening",
    "Bloomery is connected": "Bloomery is gekoppel",
    "Notifications work! You'll hear from me when there's something worth knowing.": (
        "Kennisgewings werk! Jy sal van my hoor wanneer daar iets is wat die moeite werd is om te weet."
    ),
    "Nothing to log": "Niks om aan te teken nie",
    # Errors
    "AI is disabled on this server. Enable it in Profile → AI assistant.": (
        "KI is op hierdie bediener afgeskakel. Skakel dit aan in Profiel → KI-assistent."
    ),
    "AI is disabled on this server. Set BLOOMERY_AI_PROVIDER to enable it.": (
        "KI is op hierdie bediener afgeskakel. Stel BLOOMERY_AI_PROVIDER om dit aan te skakel."
    ),
    "Backup file is too large": "Rugsteunlêer is te groot",
    "Choose the start date": "Kies die begindatum",
    "Current password is wrong": "Huidige wagwoord is verkeerd",
    "Face ID / fingerprint check failed. Use your PIN.": "Face ID-/vingerafdrukkontrole het misluk. Gebruik jou PIN.",
    "Face ID / fingerprint unlock needs Bloomery to be opened over HTTPS": (
        "Ontsluiting met Face ID/vingerafdruk vereis dat Bloomery oor HTTPS oopgemaak word"
    ),
    "Google Drive isn't connected": "Google Drive is nie gekoppel nie",
    "Google only allows HTTPS addresses (or localhost)": "Google laat net HTTPS-adresse (of localhost) toe",
    "Invalid or missing API key": "Ongeldige of ontbrekende API-sleutel",
    "Invalid username or password": "Ongeldige gebruikersnaam of wagwoord",
    "No Face ID / fingerprint set up for this address": "Geen Face ID/vingerafdruk vir hierdie adres opgestel nie",
    "No logged cycle starts on that date": "Geen aangetekende siklus begin op daardie datum nie",
    "Only the server owner (first account) can change AI settings": (
        "Slegs die bedienereienaar (eerste rekening) kan KI-instellings verander"
    ),
    "Password is wrong": "Wagwoord is verkeerd",
    "Range too large": "Reeks te groot",
    "Registration is closed": "Registrasie is gesluit",
    "Save the Google client ID and secret first": "Stoor eers die Google-kliënt-ID en -geheim",
    "Start again": "Begin weer",
    "That backup is damaged or isn't from Bloomery.": "Daardie rugsteun is beskadig of kom nie van Bloomery af nie.",
    "That isn't a Bloomery backup.": "Dit is nie 'n Bloomery-rugsteun nie.",
    "That temperature doesn't look like a body temperature": "Daardie temperatuur lyk nie na 'n liggaamstemperatuur nie",
    "The backup file is damaged.": "Die rugsteunlêer is beskadig.",
    "This backup is encrypted. Enter its passphrase.": "Hierdie rugsteun is geënkripteer. Voer sy wagfrase in.",
    "This link is no longer active": "Hierdie skakel is nie meer aktief nie",
    "Too many failed attempts. Try again in 15 minutes.": "Te veel mislukte pogings. Probeer weer oor 15 minute.",
    "Too many wrong PINs. Log in with your password.": "Te veel verkeerde PIN's. Teken aan met jou wagwoord.",
    "Turn on notifications for this device or enter a notification URL first": (
        "Skakel eers kennisgewings vir hierdie toestel aan of voer 'n kennisgewing-URL in"
    ),
    "Unknown device. Use your PIN.": "Onbekende toestel. Gebruik jou PIN.",
    "Use a passphrase of at least 8 characters": "Gebruik 'n wagfrase van minstens 8 karakters",
    "Unknown: {items}. See GET /api/quick/catalog": "Onbekend: {items}. Sien GET /api/quick/catalog",
    "Username taken": "Gebruikersnaam is reeds geneem",
    "Wrong passphrase, or the file is damaged.": "Verkeerde wagfrase, of die lêer is beskadig.",
}
