"""Lista española propia, explícita y versionada; no descarga corpus de NLTK."""

STOPWORDS_VERSION = "reviewiq-es-1"
NEGATIONS = frozenset({
    "no", "ni", "sin", "nunca", "jamás", "jamas", "tampoco", "nada", "nadie",
    "ningún", "ningun", "ninguno", "ninguna",
})
# Artículos, pronombres, preposiciones y formas auxiliares. No retirar palabras
# de valoración como bien, mal, mejor, peor, bueno, malo, mucho o poco.
BASE_STOPWORDS = frozenset("""
a al algo algunas algunos ante antes aquel aquella aquellas aquellos aquí asi así
aun aunque bajo cada como con contra cual cuales cuando de del desde donde durante
e el ella ellas ello ellos en entre era erais eran eras eres es esa esas ese esos
esta estaba estabais estaban estabas estad estamos estan estar estas este esto estos
estoy está están fue fuera fueran fueron fui fuimos ha haber habia han has hasta hay
había he hemos la las le les lo los me mi mis mientras mí nos nosotros nuestra
nuestras nuestro nuestros o os otra otras otro otros para pero por porque que quien
quienes qué se sea sean ser si sido siendo sobre sois somos son soy su sus te tiene
tienen tu tus tú un una unas uno unos usted ustedes ya yo y no ni sin nunca jamás
""".split())


def get_stopwords(
    protect_negations: bool = True, extra_stopwords: tuple[str, ...] = ()
) -> frozenset[str]:
    words = BASE_STOPWORDS | {word.casefold() for word in extra_stopwords}
    return frozenset(words - NEGATIONS if protect_negations else words)
