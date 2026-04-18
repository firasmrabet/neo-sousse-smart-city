"""
IA Strict Validator V3 - Neo-Sousse Smart City
Validates technician intervention reports using rule-based analysis.
Provides approval scoring, confidence levels, and structured reports.
"""

import re
from datetime import datetime


class StrictIAValidator:
    """
    Strict IA Validator for technician intervention reports.
    Uses rule-based heuristics to evaluate report quality,
    consistency, and assign approval scores.
    """

    def __init__(self):
        self.min_report_length = 20
        self.quality_keywords = [
            'réparé', 'remplacé', 'vérifié', 'testé', 'installé',
            'nettoyé', 'calibré', 'ajusté', 'mis à jour', 'configuré',
            'repaired', 'replaced', 'verified', 'tested', 'installed',
            'cleaned', 'calibrated', 'adjusted', 'updated', 'configured',
            'maintenance', 'diagnostic', 'inspection', 'intervention',
            'sensor', 'capteur', 'résolu', 'corrigé', 'fixed', 'resolved'
        ]
        self.risk_keywords = [
            'danger', 'urgence', 'critique', 'panne', 'défaillance',
            'urgent', 'critical', 'failure', 'broken', 'hazard'
        ]

    def _score_report(self, report_text: str) -> dict:
        """Score a single technician report based on quality metrics."""
        if not report_text or len(report_text.strip()) < self.min_report_length:
            return {
                'score': 15,
                'detail': 'Report too short or empty',
                'quality': 'INSUFFICIENT'
            }

        text_lower = report_text.lower()
        length = len(report_text.strip())

        # Base score from length (max 30 points)
        length_score = min(30, length / 10)

        # Quality keywords score (max 40 points)
        keyword_hits = sum(1 for kw in self.quality_keywords if kw in text_lower)
        keyword_score = min(40, keyword_hits * 8)

        # Structure score (max 15 points) - checks for sentences, punctuation
        sentence_count = len(re.findall(r'[.!?]+', report_text))
        structure_score = min(15, sentence_count * 3)

        # Detail score (max 15 points) - checks for numbers, dates, specifics
        has_numbers = len(re.findall(r'\d+', report_text))
        detail_score = min(15, has_numbers * 3)

        total = int(min(100, length_score + keyword_score + structure_score + detail_score))

        if total >= 75:
            quality = 'EXCELLENT'
        elif total >= 55:
            quality = 'GOOD'
        elif total >= 35:
            quality = 'ACCEPTABLE'
        else:
            quality = 'INSUFFICIENT'

        return {
            'score': total,
            'detail': f'Length:{length_score:.0f} Keywords:{keyword_score:.0f} Structure:{structure_score:.0f} Detail:{detail_score:.0f}',
            'quality': quality
        }

    def validate_reports(self, intervention_id: int, report_tech1: str, report_tech2: str) -> dict:
        """
        Validate two technician reports for an intervention.
        Returns approval level, confidence, and individual scores.
        """
        score1_data = self._score_report(report_tech1 or '')
        score2_data = self._score_report(report_tech2 or '')

        tech1_score = score1_data['score']
        tech2_score = score2_data['score']
        avg_score = (tech1_score + tech2_score) / 2

        # Confidence based on report quality consistency
        score_diff = abs(tech1_score - tech2_score)
        if score_diff < 15:
            confidence = 0.95
        elif score_diff < 30:
            confidence = 0.80
        elif score_diff < 50:
            confidence = 0.60
        else:
            confidence = 0.40

        # Approval level
        if avg_score >= 70 and confidence >= 0.7:
            approval_level = 'APPROVED ✅'
        elif avg_score >= 50:
            approval_level = 'CONDITIONALLY APPROVED ⚠️'
        elif avg_score >= 30:
            approval_level = 'REVIEW REQUIRED 🔍'
        else:
            approval_level = 'REJECTED ❌'

        # Reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Tech1 report scored {tech1_score}/100 ({score1_data['quality']})")
        reasoning_parts.append(f"Tech2 report scored {tech2_score}/100 ({score2_data['quality']})")
        reasoning_parts.append(f"Average score: {avg_score:.1f}/100")
        reasoning_parts.append(f"Score consistency: {'Good' if score_diff < 20 else 'Variable'} (diff={score_diff})")

        if any(kw in (report_tech1 or '').lower() for kw in self.risk_keywords):
            reasoning_parts.append("⚠️ Risk keywords detected in Tech1 report")
        if any(kw in (report_tech2 or '').lower() for kw in self.risk_keywords):
            reasoning_parts.append("⚠️ Risk keywords detected in Tech2 report")

        return {
            'intervention_id': intervention_id,
            'tech1_score': tech1_score,
            'tech2_score': tech2_score,
            'tech1_quality': score1_data['quality'],
            'tech2_quality': score2_data['quality'],
            'tech1_detail': score1_data['detail'],
            'tech2_detail': score2_data['detail'],
            'average_score': avg_score,
            'confidence': confidence,
            'approval_level': approval_level,
            'reasoning': '\n'.join(reasoning_parts),
            'timestamp': datetime.now().isoformat()
        }

    def generate_strict_report(self, intervention_id: int, report_tech1: str, report_tech2: str, validation: dict) -> str:
        """Generate a full text report from the validation results."""
        report = []
        report.append("=" * 70)
        report.append(f"IA STRICT VALIDATION REPORT — Intervention #{intervention_id}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        report.append("")
        report.append(f"APPROVAL: {validation.get('approval_level', 'N/A')}")
        report.append(f"CONFIDENCE: {validation.get('confidence', 0) * 100:.0f}%")
        report.append(f"AVERAGE SCORE: {validation.get('average_score', 0):.1f}/100")
        report.append("")
        report.append("-" * 40)
        report.append("TECHNICIAN 1 (Intervenant)")
        report.append(f"  Score: {validation.get('tech1_score', 0)}/100")
        report.append(f"  Quality: {validation.get('tech1_quality', 'N/A')}")
        report.append(f"  Detail: {validation.get('tech1_detail', '')}")
        report.append(f"  Report excerpt: {(report_tech1 or '')[:200]}")
        report.append("")
        report.append("-" * 40)
        report.append("TECHNICIAN 2 (Validateur)")
        report.append(f"  Score: {validation.get('tech2_score', 0)}/100")
        report.append(f"  Quality: {validation.get('tech2_quality', 'N/A')}")
        report.append(f"  Detail: {validation.get('tech2_detail', '')}")
        report.append(f"  Report excerpt: {(report_tech2 or '')[:200]}")
        report.append("")
        report.append("-" * 40)
        report.append("REASONING")
        report.append(validation.get('reasoning', 'No reasoning available'))
        report.append("")
        report.append("=" * 70)
        report.append("End of IA Strict Validation Report")
        report.append("=" * 70)

        return "\n".join(report)


def suggest_rephrase(nl_query: str) -> str:
    """
    Suggest a better phrasing for a natural language query.
    This is a rule-based fallback when Ollama is not available.
    """
    if not nl_query or not nl_query.strip():
        return "Please enter a natural language query first."

    suggestions = {
        'capteur': "Essayez: 'Afficher tous les capteurs avec leur statut et localisation'",
        'sensor': "Try: 'Show all sensors with status and location'",
        'intervention': "Essayez: 'Lister les interventions récentes avec leurs techniciens assignés'",
        'technicien': "Essayez: 'Afficher les techniciens et le nombre d'interventions effectuées'",
        'pollution': "Essayez: 'Quelles sont les 5 zones les plus polluées dans les dernières 24h?'",
        'citoyen': "Essayez: 'Afficher les citoyens avec le meilleur score d'engagement'",
        'véhicule': "Essayez: 'Lister les véhicules électriques et leur consommation CO2'",
        'trajet': "Essayez: 'Montrer les trajets avec la plus grande économie de CO2'",
    }

    nl_lower = nl_query.lower()
    for keyword, suggestion in suggestions.items():
        if keyword in nl_lower:
            return suggestion

    return f"Suggestion: Soyez plus spécifique. Par exemple: 'Afficher les [entité] où [condition] ordonnés par [critère]'. Votre requête: '{nl_query}'"
