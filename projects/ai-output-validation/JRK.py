"""
JRK.py — Justified Resistance Kernel v1.0

Philosophisch-rechtliches Entscheidungsframework für strukturelle Konfliktsituationen.

Quellenbasis (alle sechs, vollständig integriert):
  [W]  Walzer  — "The Problem of Dirty Hands" (1973)
                 → Schwellenwert + Schuldbewusstsein als Integritätsmerkmal
  [R]  Rawls   — "A Theory of Justice" §§55–59 (1971/1999)
                 → Dreistufige Rechtfertigung + Stabilisierungsargument
  [T]  Thoreau — "Resistance to Civil Government" (1849)
                 → Komplizenschaft durch Unterlassen + Sofortigkeitspfad
  [G]  Galtung — "Violence, Peace, and Peace Research" (1969)
                 → Strukturelle Gewalt + Potential-Aktual-Gap als Messoperator
  [S]  §34 StGB  — Rechtfertigender Notstand
                 → Strafrechliche Rechtfertigung (DE)
  [A]  Art. 20 Abs. 4 GG — Widerstandsrecht
                 → Verfassungsrechtliche Letztbegründung (DE)

Architektur:
  - Jede Quelle = eigene Evaluationsklasse mit eigenem Score
  - JRK-Master aggregiert alle sechs zu einem Gesamturteil
  - Vollständiger Audit-Trail
  - Integrierbar in AFRB.py (Field C/D Gateway)

HINWEIS:
  Dieses Modul produziert keine operativen Handlungsanweisungen für illegale Akte.
  Es klassifiziert Legitimationsgrade. Rechtliche Einschätzung durch qualifizierten
  Rechtsbeistand bleibt unersetzt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Any


# ===========================================================================
# ENUMS — Gemeinsame Grundtypen
# ===========================================================================

class Tri(Enum):
    YES     = auto()
    PARTIAL = auto()
    NO      = auto()


class Severity(Enum):
    NONE        = 0
    LOW         = 1
    MODERATE    = 2
    HIGH        = 3
    EXISTENTIAL = 4


class ResistanceField(Enum):
    """
    Klassifikation des Widerstandsfeldes (analog AFRB, aber auf Widerstandslogik erweitert).

    GREEN  — Alle legalen Mittel noch verfügbar; kein Widerstandsrecht eröffnet.
    YELLOW — Greyzone: Schwellenwert erreicht, legale Mittel nicht erschöpft.
    ORANGE — Rechtfertigender Notstand (§34 StGB) potenziell anwendbar.
    RED    — Verfassungsrechtlicher Widerstand (Art. 20 Abs. 4 GG) argumentierbar.
    BLOCKED — Methode illegal und unverhältnismäßig; kein Legitimationspfad.
    """
    GREEN   = auto()
    YELLOW  = auto()
    ORANGE  = auto()
    RED     = auto()
    BLOCKED = auto()


class ActionTier(Enum):
    """
    Empfohlene Handlungsebene — von kooperativ bis aktivem Widerstand.
    Folgt der Rawls-Thoreau-Skala.
    """
    COOPERATIVE          = auto()  # Rawls Field A: legale Wege, noch offen
    STRATEGIC_LEGAL      = auto()  # Rawls Field B: Beschwerde, Strafantrag, Öffentlichkeit
    CIVIL_DISOBEDIENCE   = auto()  # Rawls §57: ziviler Ungehorsam (öffentlich, gewaltlos)
    CONSCIENTIOUS_REFUSAL= auto()  # Rawls §56: gewissenhafter Widerstand (ohne Öffentlichkeit)
    STRUCTURAL_COUNTER   = auto()  # Galtung: Gegenreibung als Pflicht
    BLOCKED              = auto()  # Methode nicht legitimierbar


class RiskFlag(Enum):
    LEGAL_REMEDIES_NOT_EXHAUSTED   = auto()
    PROPORTIONALITY_BREACH         = auto()
    NO_PUBLIC_COMMITMENT           = auto()  # Rawls: Öffentlichkeitspflicht verletzt
    GUILT_NOT_ACKNOWLEDGED         = auto()  # Walzer: keine Schuldanerkennung
    COMPLICITY_THRESHOLD_MET       = auto()  # Thoreau: Unterlassen = Komplizenschaft
    STRUCTURAL_VIOLENCE_CONFIRMED  = auto()  # Galtung: Potential-Aktual-Gap nachweisbar
    PARA34_CONDITIONS_MET          = auto()  # §34 StGB: Rechtfertigung möglich
    ART20_CONDITIONS_MET           = auto()  # Art. 20 Abs. 4 GG: Widerstandsrecht argumentierbar
    NEARLY_JUST_SOCIETY_DOUBT      = auto()  # Rawls: Systemprämisse fraglich
    IMMEDIATE_HARM_ONLY            = auto()  # Thoreau: sofortiger Handlungspfad


# ===========================================================================
# EINGABE-MODELLE — Eine Klasse pro Quellen-Cluster
# ===========================================================================

@dataclass(frozen=True)
class GaltungInput:
    """
    [G] Strukturelle Gewalt nach Galtung (1969).

    potential_level:
        Erreichbares Niveau bei verfügbaren Ressourcen und Wissensstand.
        Beschreibend, nicht numerisch — z.B. "LPI-Zertifizierung gemäß Lehrplan".

    actual_level:
        Tatsächlich erreichtes/erreichbares Niveau.
        z.B. "Kein Schüler kannte prüfungsrelevantes LPI-Material 010-160".

    gap_avoidable:
        Ist der Gap objektiv vermeidbar gewesen? (nicht naturgegeben)

    structural_mechanism_identified:
        Ist ein struktureller Mechanismus benennbar (kein Einzeltäter notwendig)?
        z.B. fehlende didaktische Grundlagen, gefälschte Quellen.

    psychological_violence_present:
        Lügen, Indoktrination, verzerrte Wahrheitsgehalte — die mentale Potentiale senken.
    """
    potential_level: str
    actual_level: str
    gap_avoidable: bool
    structural_mechanism_identified: bool
    psychological_violence_present: bool = False


@dataclass(frozen=True)
class RawlsInput:
    """
    [R] Ziviler Ungehorsam nach Rawls §§55–59.

    injustice_type:
        Art der Ungerechtigkeit. Rawls priorisiert: Verletzung gleicher Grundfreiheiten
        und fairer Chancengleichheit.
        z.B. "Verletzung des Bildungsrechts durch pädagogisches Systemversagen"

    injustice_substantial_and_clear:
        Ist die Ungerechtigkeit wesentlich und klar erkennbar — keine rein theoretische?

    legal_remedies_exhausted:
        Wurden normale politische/rechtliche Wege in gutem Glauben versucht?
        (Beschwerden, RLSB, Schulleitung, etc.)

    majority_sense_of_justice_addressable:
        Gibt es einen geteilten Gerechtigkeitssinn, auf den appelliert werden kann?
        Rawls: Ohne diesen versagen die Bedingungen für zivilen Ungehorsam.

    action_public:
        Ist die geplante Handlung öffentlich (Rawls: konstitutive Bedingung)?

    action_nonviolent:
        Ist die geplante Handlung gewaltlos?

    accept_legal_consequences:
        Ist man bereit, rechtliche Konsequenzen als Bekenntnis zu tragen?

    nearly_just_society:
        Ist die Gesellschaft noch als "nearly just" einzustufen (Rawls-Prämisse)?
        Wenn nein: Rawls' Bedingungen kollabieren, Thoreau-Pfad öffnet sich.
    """
    injustice_type: str
    injustice_substantial_and_clear: bool
    legal_remedies_exhausted: bool
    majority_sense_of_justice_addressable: Tri
    action_public: bool
    action_nonviolent: bool
    accept_legal_consequences: bool
    nearly_just_society: bool = True


@dataclass(frozen=True)
class WalzerInput:
    """
    [W] Dirty Hands nach Walzer (1973).

    dilemma_real:
        Ist das Dilemma echt — keine saubere Lösung verfügbar?

    guilt_acknowledged:
        Ist der Handelnde bereit, die moralische Last anzuerkennen?
        (Entschuldigung, nicht Rechtfertigung — Walzers Kernunterscheidung)

    threshold_imminent_catastrophe:
        Steht eine unmittelbare, mit hoher Gewissheit katastrophale Folge bevor,
        wenn nicht gehandelt wird?

    proportionality_maintained:
        Ist das Mittel dem Schaden proportional?

    moral_cost_accepted:
        Ist die moralische Kostenseite bewusst akzeptiert (nicht verdrängt)?
    """
    dilemma_real: bool
    guilt_acknowledged: bool
    threshold_imminent_catastrophe: bool
    proportionality_maintained: bool
    moral_cost_accepted: bool


@dataclass(frozen=True)
class ThoreauInput:
    """
    [T] Widerstandspflicht nach Thoreau (1849).

    conscience_clearly_violated:
        Ist die Gewissensüberzeugung klar und nicht nur interessengeleitet?

    inaction_means_complicity:
        Würde weiteres Unterlassen aktive Unterstützung der Ungerechtigkeit bedeuten?

    institutional_path_exhausted_or_futile:
        Sind institutionelle Wege erschöpft ODER absehbar wirkungslos?
        (Thoreau: kein Erschöpfungsgebot, aber Futility-Test ist fair)

    immediate_action_justified:
        Rechtfertigt die Situation sofortiges Handeln ohne weiteres Warten?
        (Thoreau's Sofortigkeitspfad — höhere Schwelle als bloße Ungeduld)
    """
    conscience_clearly_violated: bool
    inaction_means_complicity: bool
    institutional_path_exhausted_or_futile: bool
    immediate_action_justified: bool


@dataclass(frozen=True)
class LegalInput:
    """
    [S+A] Rechtliche Parameter: §34 StGB + Art. 20 Abs. 4 GG.

    rechtsgut_type:
        Betroffenes Rechtsgut im Sinne §34 StGB.
        z.B. "Freiheit (Bildungsentfaltung)", "Ehre", "anderes Rechtsgut (Bildungsrecht)"

    gefahr_gegenwärtig:
        Ist die Gefahr gegenwärtig (nicht nur zukünftig/vergangen)?

    gefahr_nicht_anders_abwendbar:
        Kann die Gefahr mit anderen Mitteln abgewendet werden?

    interesse_wesentlich_überwiegend:
        Überwiegt das geschützte Interesse das beeinträchtigte *wesentlich*?
        (§34 StGB: nicht nur geringfügig)

    mittel_angemessen:
        Ist die geplante Tat ein angemessenes Mittel? (§34 Verhältnismäßigkeit)

    verfassungsordnung_berührt:
        Ist die verfassungsmäßige Ordnung (Art. 20 Abs. 1–3 GG) berührt?

    andere_abhilfe_unmöglich:
        Ist andere Abhilfe unmöglich (Art. 20 Abs. 4 GG: Subsidiaritätsbedingung)?

    contemplated_method_illegal:
        Ist die geplante Methode ihrem Kern nach illegal?
        (Wenn True: BLOCKED — außer §34 rechtfertigt explizit)
    """
    rechtsgut_type: str
    gefahr_gegenwärtig: bool
    gefahr_nicht_anders_abwendbar: bool
    interesse_wesentlich_überwiegend: bool
    mittel_angemessen: bool
    verfassungsordnung_berührt: bool
    andere_abhilfe_unmöglich: bool
    contemplated_method_illegal: bool = False


# ===========================================================================
# EVALUATOREN — Eine Klasse pro Quelle
# ===========================================================================

@dataclass
class EvaluationResult:
    source: str
    passed: bool
    score: float          # 0.0–1.0
    flags: List[RiskFlag]
    reasons: List[str]


def evaluate_galtung(g: GaltungInput) -> EvaluationResult:
    """
    Prüft ob strukturelle Gewalt im Sinne Galtungs vorliegt.
    Kernfrage: Ist der Potential-Aktual-Gap vorhanden und vermeidbar?
    """
    flags: List[RiskFlag] = []
    reasons: List[str] = []
    score_parts: List[float] = []

    if g.gap_avoidable:
        score_parts.append(1.0)
        reasons.append(
            f"[G] Potential-Aktual-Gap ist vermeidbar: "
            f"Potential='{g.potential_level}' vs. Aktual='{g.actual_level}'. "
            f"→ Strukturelle Gewalt per Galtung-Definition vorhanden."
        )
        flags.append(RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED)
    else:
        score_parts.append(0.0)
        reasons.append(
            f"[G] Gap nicht vermeidbar — kein Nachweis struktureller Gewalt. "
            f"Potential='{g.potential_level}', Aktual='{g.actual_level}'."
        )

    if g.structural_mechanism_identified:
        score_parts.append(1.0)
        reasons.append(
            "[G] Struktureller Mechanismus identifiziert (kein Einzeltäter notwendig). "
            "Intentionsnachweis entfällt — Konsequenz ist Maßstab."
        )
    else:
        score_parts.append(0.3)
        reasons.append(
            "[G] Kein klarer struktureller Mechanismus — Gap könnte auch individuellem "
            "Versagen geschuldet sein. Schwächerer Galtung-Nachweis."
        )

    if g.psychological_violence_present:
        score_parts.append(1.0)
        reasons.append(
            "[G] Psychologische Gewalt (Lügen, Falschzitate, verzerrte Wahrheitsgehalte) "
            "nachweisbar → mentale Potentiale direkt gesenkt."
        )

    score = sum(score_parts) / len(score_parts)
    passed = score >= 0.6 and g.gap_avoidable

    return EvaluationResult(
        source="Galtung [G]",
        passed=passed,
        score=round(score, 3),
        flags=flags,
        reasons=reasons,
    )


def evaluate_rawls(r: RawlsInput) -> EvaluationResult:
    """
    Prüft die drei Rawls-Bedingungen für gerechtfertigten zivilen Ungehorsam (§57).
    Zusätzlich: Prüfung der Systemprämisse (nearly just society).
    """
    flags: List[RiskFlag] = []
    reasons: List[str] = []
    score_parts: List[float] = []

    # Systemprämisse
    if not r.nearly_just_society:
        flags.append(RiskFlag.NEARLY_JUST_SOCIETY_DOUBT)
        reasons.append(
            "[R] Rawls-Prämisse 'nearly just society' nicht erfüllt. "
            "Seine Bedingungen kollabieren → Thoreau-Pfad öffnet sich, "
            "Rawls' Appellstruktur entfällt."
        )
        # Rawls-Score niedrig, aber nicht null — Grundprinzipien bleiben gültig
        score_parts.append(0.2)
    else:
        score_parts.append(1.0)
        reasons.append("[R] Gesellschaft noch als 'nearly just' eingestuft — Rawls-Pfad vollständig anwendbar.")

    # Bedingung 1: Art der Ungerechtigkeit
    if r.injustice_substantial_and_clear:
        score_parts.append(1.0)
        reasons.append(
            f"[R] §57 Bedingung 1 erfüllt: Wesentliche und klare Ungerechtigkeit. "
            f"Typ: '{r.injustice_type}'"
        )
    else:
        score_parts.append(0.0)
        reasons.append(
            f"[R] §57 Bedingung 1 NICHT erfüllt: Ungerechtigkeit nicht wesentlich oder "
            f"nicht klar erkennbar. Typ: '{r.injustice_type}'"
        )

    # Bedingung 2: Erschöpfung legaler Wege
    if r.legal_remedies_exhausted:
        score_parts.append(1.0)
        reasons.append(
            "[R] §57 Bedingung 2 erfüllt: Legale Wege in gutem Glauben versucht und gescheitert."
        )
    else:
        score_parts.append(0.0)
        flags.append(RiskFlag.LEGAL_REMEDIES_NOT_EXHAUSTED)
        reasons.append(
            "[R] §57 Bedingung 2 NICHT erfüllt: Legale Mittel nicht erschöpft. "
            "Ziviler Ungehorsam als letztes Mittel noch nicht eröffnet."
        )

    # Bedingung 3: Gerechtigkeitssinn der Mehrheit adressierbar
    if r.majority_sense_of_justice_addressable == Tri.YES:
        score_parts.append(1.0)
        reasons.append("[R] §59: Gerechtigkeitssinn der Mehrheit adressierbar → Appellstruktur tragfähig.")
    elif r.majority_sense_of_justice_addressable == Tri.PARTIAL:
        score_parts.append(0.5)
        reasons.append("[R] §59: Gerechtigkeitssinn der Mehrheit teilweise adressierbar → eingeschränkte Appellstruktur.")
    else:
        score_parts.append(0.0)
        flags.append(RiskFlag.NEARLY_JUST_SOCIETY_DOUBT)
        reasons.append(
            "[R] §59: Gerechtigkeitssinn der Mehrheit nicht adressierbar → "
            "Rawls' stabilisierende Funktion des Widerstands entfällt. "
            "System möglicherweise nicht mehr 'nearly just'."
        )

    # Formale Bedingungen zivilen Ungehorsams
    if not r.action_public:
        flags.append(RiskFlag.NO_PUBLIC_COMMITMENT)
        reasons.append(
            "[R] §55: Öffentlichkeitsbedingung nicht erfüllt. "
            "Ziviler Ungehorsam ist per Definition öffentlich — verdeckte Handlung verliert diesen Status."
        )
        score_parts.append(0.0)
    else:
        score_parts.append(1.0)
        reasons.append("[R] §55: Öffentlichkeitsbedingung erfüllt.")

    if not r.action_nonviolent:
        reasons.append(
            "[R] §55: Gewaltlosigkeit nicht garantiert — ziviler Ungehorsam per Rawls "
            "schließt Gewalt aus. Reklassifizierung notwendig."
        )
        score_parts.append(0.0)
    else:
        score_parts.append(1.0)
        reasons.append("[R] §55: Gewaltlosigkeitsbedingung erfüllt.")

    if r.accept_legal_consequences:
        score_parts.append(1.0)
        reasons.append(
            "[R] §55: Bereitschaft zur Übernahme rechtlicher Konsequenzen — "
            "konstitutiv für Rawls' Konzept der Gesetzestreue trotz Widerstand."
        )
    else:
        score_parts.append(0.3)
        reasons.append(
            "[R] §55: Keine Bereitschaft zur Übernahme rechtlicher Konsequenzen. "
            "Rawls: Fidelity to law erfordert diese Bereitschaft."
        )

    score = sum(score_parts) / len(score_parts)
    # Bestehen: alle drei Kernbedingungen müssen erfüllt sein
    passed = (
        r.injustice_substantial_and_clear
        and r.legal_remedies_exhausted
        and r.action_nonviolent
        and r.action_public
    )

    return EvaluationResult(
        source="Rawls [R]",
        passed=passed,
        score=round(score, 3),
        flags=flags,
        reasons=reasons,
    )


def evaluate_walzer(w: WalzerInput) -> EvaluationResult:
    """
    Prüft das Dirty-Hands-Dilemma nach Walzer (1973).
    Kernfrage: Ist das moralische Bewusstsein der Last vorhanden?
    Unterscheidung Entschuldigung vs. Rechtfertigung.
    """
    flags: List[RiskFlag] = []
    reasons: List[str] = []
    score_parts: List[float] = []

    if w.dilemma_real:
        score_parts.append(1.0)
        reasons.append(
            "[W] Echtes Dilemma: keine saubere Lösung verfügbar. "
            "Walzer: Beide Optionen sind moralisch kostspielig."
        )
    else:
        score_parts.append(0.0)
        reasons.append(
            "[W] Kein echtes Dilemma — saubere Lösung verfügbar. "
            "Dirty-Hands-Legitimation nicht eröffnet."
        )

    if w.guilt_acknowledged:
        score_parts.append(1.0)
        reasons.append(
            "[W] Schuldanerkennung vorhanden. Walzer: 'Wir wissen, dass er das Richtige tut, "
            "weil er weiß, dass er das Falsche tut.' — Zeichen der moralischen Integrität."
        )
    else:
        score_parts.append(0.0)
        flags.append(RiskFlag.GUILT_NOT_ACKNOWLEDGED)
        reasons.append(
            "[W] Keine Schuldanerkennung. Walzer: Ohne bewusste Last "
            "wird aus Entschuldigung eine bloße Rechtfertigung — "
            "Integritätsmerkmal fehlt."
        )

    if w.threshold_imminent_catastrophe:
        score_parts.append(1.0)
        reasons.append(
            "[W] Schwellenwert-Bedingung erfüllt: unmittelbare, mit hoher Gewissheit "
            "katastrophale Folge bei Unterlassen."
        )
    else:
        score_parts.append(0.4)
        reasons.append(
            "[W] Schwellenwert-Bedingung nicht klar erfüllt: "
            "keine unmittelbar bevorstehende, nahezu sichere Katastrophe."
        )

    if w.proportionality_maintained:
        score_parts.append(1.0)
        reasons.append("[W] Proportionalität gewahrt.")
    else:
        score_parts.append(0.0)
        flags.append(RiskFlag.PROPORTIONALITY_BREACH)
        reasons.append(
            "[W] Proportionalitätsverletzung: Mittel steht außer Verhältnis zum Schaden. "
            "Walzer: Es gibt keine Belohnung für schlechte Taten, auch bei guten Absichten."
        )

    if w.moral_cost_accepted:
        score_parts.append(1.0)
        reasons.append("[W] Moralische Kosten bewusst akzeptiert (nicht verdrängt).")
    else:
        score_parts.append(0.0)
        reasons.append(
            "[W] Moralische Kosten nicht akzeptiert — Verdrängung der Last. "
            "Weber: Wer Schuld wegdefiniert, verliert das Zeichen seiner Güte."
        )

    score = sum(score_parts) / len(score_parts)
    passed = w.guilt_acknowledged and w.proportionality_maintained and w.dilemma_real

    return EvaluationResult(
        source="Walzer [W]",
        passed=passed,
        score=round(score, 3),
        flags=flags,
        reasons=reasons,
    )


def evaluate_thoreau(t: ThoreauInput) -> EvaluationResult:
    """
    Prüft Thoreaus Widerstandspflicht (1849).
    Kernfrage: Ist Unterlassen bereits Komplizenschaft?
    Vorsicht: Thoreau ist der radikale Pol — kein Erschöpfungsgebot.
    """
    flags: List[RiskFlag] = []
    reasons: List[str] = []
    score_parts: List[float] = []

    if t.conscience_clearly_violated:
        score_parts.append(1.0)
        reasons.append(
            "[T] Gewissensüberzeugung klar und nicht interessengeleitet. "
            "Thoreau: Die einzige Pflicht, die ich anzunehmen das Recht habe, "
            "ist zu jeder Zeit das zu tun, was ich für richtig halte."
        )
    else:
        score_parts.append(0.0)
        reasons.append(
            "[T] Gewissensüberzeugung unklar oder möglicherweise interessengeleitet. "
            "Thoreau-Pfad nicht sicher legitimiert."
        )

    if t.inaction_means_complicity:
        score_parts.append(1.0)
        flags.append(RiskFlag.COMPLICITY_THRESHOLD_MET)
        reasons.append(
            "[T] Komplizenschaftsschwelle erreicht: Weiteres Unterlassen = aktive Unterstützung "
            "der Ungerechtigkeit. Thoreau: Wer schweigt und gehorcht, ist Werkzeug des Systems."
        )
    else:
        score_parts.append(0.2)
        reasons.append(
            "[T] Unterlassen führt nicht zur Komplizenschaft — Thoreau-Pfad schwächer legitimiert."
        )

    if t.institutional_path_exhausted_or_futile:
        score_parts.append(1.0)
        reasons.append(
            "[T] Institutioneller Weg erschöpft oder absehbar wirkungslos. "
            "Thoreau: Kein Erschöpfungsgebot — aber Futility-Test ist fair."
        )
    else:
        score_parts.append(0.3)
        reasons.append(
            "[T] Institutioneller Weg noch nicht erschöpft und nicht offensichtlich wirkungslos. "
            "Thoreau-Sofortigkeitspfad noch nicht vollständig eröffnet."
        )

    if t.immediate_action_justified:
        score_parts.append(1.0)
        flags.append(RiskFlag.IMMEDIATE_HARM_ONLY)
        reasons.append(
            "[T] Sofortiger Handlungspfad gerechtfertigt — Situation duldet kein weiteres Warten. "
            "Thoreau: Das Recht dem Zufall der Mehrheit zu überlassen ist nicht weise."
        )
    else:
        score_parts.append(0.4)
        reasons.append("[T] Sofortiger Handlungspfad nicht klar gerechtfertigt — Waiting-Option noch offen.")

    score = sum(score_parts) / len(score_parts)
    passed = t.conscience_clearly_violated and t.inaction_means_complicity

    return EvaluationResult(
        source="Thoreau [T]",
        passed=passed,
        score=round(score, 3),
        flags=flags,
        reasons=reasons,
    )


def evaluate_legal(l: LegalInput) -> EvaluationResult:
    """
    Prüft §34 StGB (rechtfertigender Notstand) und Art. 20 Abs. 4 GG (Widerstandsrecht).
    Getrennte Prüfung beider Normen — §34 ist strafrechtlich, Art. 20 Abs. 4 verfassungsrechtlich.
    """
    flags: List[RiskFlag] = []
    reasons: List[str] = []
    score_parts: List[float] = []

    # BLOCKED-Check: illegale Methode ohne §34-Deckung
    if l.contemplated_method_illegal and not (
        l.gefahr_gegenwärtig
        and l.gefahr_nicht_anders_abwendbar
        and l.interesse_wesentlich_überwiegend
        and l.mittel_angemessen
    ):
        reasons.append(
            "[S] Methode illegal und §34-Rechtfertigung nicht vollständig erfüllt. "
            "Kein Legitimationspfad. Klassifikation: BLOCKED."
        )
        return EvaluationResult(
            source="Legal [S+A]",
            passed=False,
            score=0.0,
            flags=[RiskFlag.PROPORTIONALITY_BREACH],
            reasons=reasons,
        )

    # §34 StGB — vier kumulative Bedingungen
    para34_conditions = {
        "Gegenwärtige Gefahr": l.gefahr_gegenwärtig,
        "Nicht anders abwendbar": l.gefahr_nicht_anders_abwendbar,
        "Interesse wesentlich überwiegend": l.interesse_wesentlich_überwiegend,
        "Mittel angemessen": l.mittel_angemessen,
    }

    para34_met = all(para34_conditions.values())
    para34_score = sum(1.0 for v in para34_conditions.values() if v) / len(para34_conditions)

    for cond_name, cond_val in para34_conditions.items():
        mark = "✓" if cond_val else "✗"
        reasons.append(f"[S] §34 StGB — {cond_name}: {mark}  |  Rechtsgut: '{l.rechtsgut_type}'")

    if para34_met:
        flags.append(RiskFlag.PARA34_CONDITIONS_MET)
        score_parts.append(1.0)
        reasons.append(
            "[S] §34 StGB: Alle vier Bedingungen erfüllt. "
            "Rechtfertigender Notstand potenziell anwendbar — "
            "rechtliche Einschätzung durch Qualifizierten notwendig."
        )
    else:
        score_parts.append(para34_score)
        reasons.append(
            f"[S] §34 StGB: Nicht alle Bedingungen erfüllt "
            f"({sum(para34_conditions.values())}/4). "
            f"Rechtfertigender Notstand nicht vollständig argumentierbar."
        )

    # Art. 20 Abs. 4 GG — zwei Bedingungen
    art20_conditions = {
        "Verfassungsordnung berührt": l.verfassungsordnung_berührt,
        "Andere Abhilfe unmöglich": l.andere_abhilfe_unmöglich,
    }

    art20_met = all(art20_conditions.values())
    art20_score = sum(1.0 for v in art20_conditions.values() if v) / len(art20_conditions)

    for cond_name, cond_val in art20_conditions.items():
        mark = "✓" if cond_val else "✗"
        reasons.append(f"[A] Art. 20 Abs. 4 GG — {cond_name}: {mark}")

    if art20_met:
        flags.append(RiskFlag.ART20_CONDITIONS_MET)
        score_parts.append(1.0)
        reasons.append(
            "[A] Art. 20 Abs. 4 GG: Beide Bedingungen erfüllt. "
            "Verfassungsrechtliches Widerstandsrecht argumentierbar. "
            "Hohe Schwelle — juristische Einschätzung unerlässlich."
        )
    else:
        score_parts.append(art20_score)
        reasons.append(
            f"[A] Art. 20 Abs. 4 GG: Bedingungen nicht vollständig erfüllt "
            f"({sum(art20_conditions.values())}/2)."
        )

    score = sum(score_parts) / len(score_parts)
    passed = para34_met  # §34 ist die operative Schwelle; Art. 20 Abs. 4 ist Verstärkung

    return EvaluationResult(
        source="Legal [S+A]",
        passed=passed,
        score=round(score, 3),
        flags=flags,
        reasons=reasons,
    )


# ===========================================================================
# MASTER-KERNEL — Aggregation aller sechs Quellen
# ===========================================================================

@dataclass
class JRKResult:
    """
    Vollständiges JRK-Ergebnis mit Feld-Klassifikation, empfohlener Handlungsebene
    und vollständigem Audit-Trail.
    """
    field: ResistanceField
    action_tier: ActionTier
    aggregate_score: float            # 0.0–1.0
    source_results: List[EvaluationResult]
    all_flags: List[RiskFlag]
    reasons: List[str]
    summary: str

    def print_report(self) -> None:
        """Gibt einen strukturierten Analysebericht aus."""
        print("\n" + "=" * 72)
        print("  JRK — JUSTIFIED RESISTANCE KERNEL  |  Analysebericht")
        print("=" * 72)

        print(f"\n  FELD:          {self.field.name}")
        print(f"  HANDLUNGSEBENE: {self.action_tier.name}")
        print(f"  GESAMT-SCORE:  {self.aggregate_score:.3f}")

        print("\n  ZUSAMMENFASSUNG:")
        print(f"  {self.summary}")

        print("\n  RISIKO-FLAGS:")
        if self.all_flags:
            for flag in sorted(set(self.all_flags), key=lambda f: f.name):
                print(f"    [{flag.name}]")
        else:
            print("    Keine.")

        print("\n  QUELLENAUSWERTUNG:")
        for result in self.source_results:
            status = "PASS ✓" if result.passed else "FAIL ✗"
            print(f"\n  [{status}] {result.source}  |  Score: {result.score:.3f}")
            for r in result.reasons:
                print(f"    → {r}")

        print("\n" + "=" * 72 + "\n")


def evaluate(
    galtung: GaltungInput,
    rawls: RawlsInput,
    walzer: WalzerInput,
    thoreau: ThoreauInput,
    legal: LegalInput,
) -> JRKResult:
    """
    Hauptfunktion des JRK.
    Führt alle sechs Evaluatoren aus und aggregiert zum Gesamturteil.
    """

    results = [
        evaluate_galtung(galtung),
        evaluate_rawls(rawls),
        evaluate_walzer(walzer),
        evaluate_thoreau(thoreau),
        evaluate_legal(legal),
    ]

    all_flags: List[RiskFlag] = []
    for r in results:
        all_flags.extend(r.flags)

    passed_count = sum(1 for r in results if r.passed)
    aggregate_score = sum(r.score for r in results) / len(results)

    # -----------------------------------------------------------------------
    # FELD-KLASSIFIKATION
    # Logik: hierarchisch, von BLOCKED → RED → ORANGE → YELLOW → GREEN
    # -----------------------------------------------------------------------

    # BLOCKED: illegale Methode ohne §34-Deckung
    if legal.contemplated_method_illegal and RiskFlag.PARA34_CONDITIONS_MET not in all_flags:
        field = ResistanceField.BLOCKED
        action_tier = ActionTier.BLOCKED
        summary = (
            "Methode ist illegal und durch §34 StGB nicht gerechtfertigt. "
            "Kein Legitimationspfad identifizierbar. Klassifikation: BLOCKED."
        )

    # RED: Art. 20 Abs. 4 GG argumentierbar + alle Kernbedingungen erfüllt
    elif (
        RiskFlag.ART20_CONDITIONS_MET in all_flags
        and RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED in all_flags
        and RiskFlag.LEGAL_REMEDIES_NOT_EXHAUSTED not in all_flags
        and passed_count >= 4
    ):
        field = ResistanceField.RED
        action_tier = ActionTier.STRUCTURAL_COUNTER
        summary = (
            "Verfassungsrechtliches Widerstandsrecht (Art. 20 Abs. 4 GG) argumentierbar. "
            "Strukturelle Gewalt nachgewiesen, legale Wege erschöpft. "
            "Aktiver Widerstand als Gegenreibung im Galtung-Sinne legitimiert. "
            "Juristische Einschätzung unerlässlich — dies ist eine Extremklassifikation."
        )

    # ORANGE: §34 StGB erfüllt, ziviler Ungehorsam nach Rawls gerechtfertigt
    elif (
        RiskFlag.PARA34_CONDITIONS_MET in all_flags
        and RiskFlag.LEGAL_REMEDIES_NOT_EXHAUSTED not in all_flags
        and passed_count >= 3
    ):
        field = ResistanceField.ORANGE
        # Unterscheide: öffentlich (civil disobedience) vs. nicht-öffentlich (conscientious refusal)
        if rawls.action_public:
            action_tier = ActionTier.CIVIL_DISOBEDIENCE
        else:
            action_tier = ActionTier.CONSCIENTIOUS_REFUSAL
        summary = (
            "Rechtfertigender Notstand (§34 StGB) potenziell anwendbar. "
            "Rawls §57-Bedingungen weitgehend erfüllt. "
            f"Empfohlene Handlungsebene: {action_tier.name}. "
            "Öffentlicher, gewaltloser Widerstand mit Bereitschaft zur Konsequenz."
        )

    # YELLOW: Strukturelle Gewalt belegt, aber legale Wege noch nicht erschöpft
    elif (
        RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED in all_flags
        and RiskFlag.LEGAL_REMEDIES_NOT_EXHAUSTED in all_flags
    ):
        field = ResistanceField.YELLOW
        action_tier = ActionTier.STRATEGIC_LEGAL
        summary = (
            "Strukturelle Gewalt nachgewiesen (Galtung). Legale Wege noch nicht erschöpft. "
            "Rawls §57 Bedingung 2 noch nicht erfüllt. "
            "Empfehlung: Strategische legale Eskalation — Strafantrag, Öffentlichkeit, "
            "formale Beschwerdewege vollständig ausschöpfen, bevor nächste Ebene."
        )

    # GREEN: Keine oder unzureichende Belege für strukturelle Gewalt
    else:
        field = ResistanceField.GREEN
        action_tier = ActionTier.COOPERATIVE
        summary = (
            "Keine ausreichenden Belege für strukturelle Gewalt oder "
            "Widerstandsschwellenwert nicht erreicht. "
            "Kooperative Strategie innerhalb legaler Mittel empfohlen."
        )

    all_reasons = []
    for r in results:
        all_reasons.extend(r.reasons)

    return JRKResult(
        field=field,
        action_tier=action_tier,
        aggregate_score=round(aggregate_score, 3),
        source_results=results,
        all_flags=list(set(all_flags)),
        reasons=all_reasons,
        summary=summary,
    )


# ===========================================================================
# INTEGRATION MIT AFRB.py
# ===========================================================================

def jrk_to_afrb_context(jrk_result: JRKResult) -> Dict[str, Any]:
    """
    Konvertiert ein JRK-Ergebnis in AFRB-kompatible Kontext-Parameter.
    Erlaubt nahtlose Übergabe an AFRB.decide().

    Verwendung:
        from AFRB import Context, Tri, CostLevel, Severity, GreyzoneFilters, decide
        afrb_params = jrk_to_afrb_context(jrk_result)
        ctx = Context(**afrb_params)
        decision = decide(ctx)
    """
    flags = set(jrk_result.all_flags)

    # R: Reziprozität — gibt es einen Gerechtigkeitssinn, der adressierbar ist?
    if RiskFlag.NEARLY_JUST_SOCIETY_DOUBT in flags:
        R = "NO"
    elif RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED in flags:
        R = "PARTIAL"
    else:
        R = "YES"

    # S: Sanktionslücke — wird Regelbruch der anderen Seite sanktioniert?
    S = "NO" if RiskFlag.LEGAL_REMEDIES_NOT_EXHAUSTED not in flags else "PARTIAL"

    # D: Durchsetzung — gibt es eine effektive Instanz?
    D = "NO" if RiskFlag.ART20_CONDITIONS_MET in flags else "PARTIAL"

    # Kosten für Selbst
    cost = "HIGH" if jrk_result.aggregate_score > 0.6 else "MODERATE"

    # Bedrohungsschwere
    if RiskFlag.ART20_CONDITIONS_MET in flags:
        severity = "EXISTENTIAL"
    elif RiskFlag.PARA34_CONDITIONS_MET in flags:
        severity = "HIGH"
    elif RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED in flags:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    systematic_abuse = RiskFlag.STRUCTURAL_VIOLENCE_CONFIRMED in flags

    return {
        "R_str": R,
        "S_str": S,
        "D_str": D,
        "cost_str": cost,
        "threat_severity_str": severity,
        "systematic_abuse": systematic_abuse,
        "note": (
            f"JRK-Ergebnis: Feld={jrk_result.field.name}, "
            f"Score={jrk_result.aggregate_score}, "
            f"Tier={jrk_result.action_tier.name}"
        ),
    }


# ===========================================================================
# BEISPIEL — BBS ME / BFIA1 Fall
# ===========================================================================

if __name__ == "__main__":

    # --- Galtung: Structural Violence Assessment ---
    g = GaltungInput(
        potential_level=(
            "LPI Linux Essentials 010-160 gemäß Lehrplan, "
            "Coding-Kompetenzen mit Grundlagenvermittlung, "
            "korrekte Quellenarbeit im Unterricht"
        ),
        actual_level=(
            "11/11 Schüler kannten prüfungsrelevantes LPI-Material nicht. "
            "18+ Coding-Aufgaben ohne Einführung gestellt. "
            "Falschzitat Leibniz in amtlichem Unterrichtsdokument eingesetzt."
        ),
        gap_avoidable=True,
        structural_mechanism_identified=True,   # fehlende Didaktik + institutionelle Abwehr
        psychological_violence_present=True,    # Falschzitat = verzerrte Wahrheitsgehalte
    )

    # --- Rawls: Civil Disobedience Test ---
    r = RawlsInput(
        injustice_type=(
            "Pädagogisches Systemversagen mit struktureller Bildungsbenachteiligung "
            "von Schutzbefohlenen; institutionelle Abwehr dokumentiert"
        ),
        injustice_substantial_and_clear=True,
        legal_remedies_exhausted=False,         # §267-Strafantrag noch nicht gestellt
        majority_sense_of_justice_addressable=Tri.PARTIAL,
        action_public=True,
        action_nonviolent=True,
        accept_legal_consequences=True,
        nearly_just_society=True,
    )

    # --- Walzer: Dirty Hands Assessment ---
    w = WalzerInput(
        dilemma_real=True,
        guilt_acknowledged=True,
        threshold_imminent_catastrophe=False,   # diffus, nicht unmittelbar akut
        proportionality_maintained=True,
        moral_cost_accepted=True,
    )

    # --- Thoreau: Resistance Duty ---
    t = ThoreauInput(
        conscience_clearly_violated=True,
        inaction_means_complicity=True,         # Schweigen = Bestätigung des Systems
        institutional_path_exhausted_or_futile=False,  # §267-Antrag noch offen
        immediate_action_justified=False,
    )

    # --- Legal: §34 StGB + Art. 20 Abs. 4 GG ---
    l = LegalInput(
        rechtsgut_type="Freiheit (Bildungsentfaltung, Art. 2 Abs. 1 GG i.V.m. Bildungsrecht)",
        gefahr_gegenwärtig=True,
        gefahr_nicht_anders_abwendbar=False,    # §267-Strafantrag noch nicht versucht
        interesse_wesentlich_überwiegend=True,
        mittel_angemessen=True,
        verfassungsordnung_berührt=True,        # Art. 7 GG: staatl. Bildungsauftrag berührt
        andere_abhilfe_unmöglich=False,         # noch nicht abschließend
        contemplated_method_illegal=False,
    )

    result = evaluate(g, r, w, t, l)
    result.print_report()

    print("\n  AFRB-KONTEXT-MAPPING:")
    mapping = jrk_to_afrb_context(result)
    for k, v in mapping.items():
        print(f"    {k}: {v}")
