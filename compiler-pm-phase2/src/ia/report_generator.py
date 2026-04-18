"""
Module IA Générative — Rapports intelligents avec Ollama/OpenAI
Conforme à l'énoncé §2.3:
  1. Génère des rapports textuels à partir des données de la base
  2. Suggère des actions aux gestionnaires
  3. Valide les transitions d'automates (option avancée)
"""

import os
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from ..db_connection import get_db
except ImportError:
    try:
        from src.db_connection import get_db
    except ImportError:
        get_db = None


# Ollama Cloud API config
OLLAMA_API_URL = "https://ollama.com/api/chat"
OLLAMA_API_KEY = "0d7c0922ab2649e1b0e3653669757728.Q-4UYLI066ySjGBU-0KiS5cj"


class AIReportGenerator:
    """
    Générateur de rapports IA — Supporte Ollama Cloud API + Ollama local + OpenAI + Fallback.
    Utilise llama3.2 via Ollama Cloud API par défaut.
    """

    def __init__(self, provider: str = "ollama_api", model: str = "llama3.2:3b"):
        self.provider = "fallback"
        self.model = model
        self.client = None
        self._init_provider(provider, model)

    def _init_provider(self, provider: str, model: str):
        if provider == "ollama_api":
            # Ollama Cloud API — uses REST with Bearer token
            try:
                import requests as _req
                self._requests = _req
                self.provider = "ollama_api"
                logger.info(f"✅ Ollama Cloud API configuré — modèle: {model}")
            except ImportError:
                logger.warning("⚠️ Module 'requests' non installé. Fallback.")
        elif provider == "ollama":
            try:
                import ollama
                ollama.list()
                self.client = ollama
                self.provider = "ollama"
                logger.info(f"✅ Ollama local connecté — modèle: {model}")
            except Exception as e:
                logger.warning(f"⚠️ Ollama local non disponible: {e}. Mode fallback.")
        elif provider == "openai":
            try:
                import openai
                key = os.getenv("OPENAI_API_KEY")
                if key:
                    self.client = openai.OpenAI(api_key=key)
                    self.provider = "openai"
                else:
                    logger.warning("⚠️ OPENAI_API_KEY non trouvé. Fallback.")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI non disponible: {e}. Fallback.")

    def _llm_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Appeler le LLM (Ollama Cloud API, Ollama local ou OpenAI)"""
        raw = ""
        try:
            if self.provider == "ollama_api":
                # Ollama Cloud REST API
                resp = self._requests.post(
                    OLLAMA_API_URL,
                    headers={
                        "Authorization": f"Bearer {OLLAMA_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.4, "num_predict": max_tokens},
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    raw = msg.get("content", "") if isinstance(msg, dict) else ""
                else:
                    logger.error(f"Ollama API error {resp.status_code}: {resp.text[:200]}")
                    return ""
            elif self.provider == "ollama":
                resp = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={"temperature": 0.4, "num_predict": max_tokens},
                )
                raw = resp.get("response", "")
            elif self.provider == "openai":
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=max_tokens,
                )
                raw = resp.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return ""
        # Strip all markdown formatting artifacts from AI output
        raw = raw.replace('**', '').replace('##', '').replace('###', '')
        raw = raw.replace('# ', '').replace('*', '')
        return raw

    # ═══════════════════════════════════════════════════════════════
    # 1. Rapport Qualité de l'Air (Énoncé §2.3.1)
    # ═══════════════════════════════════════════════════════════════

    def generate_air_quality_report(self, sensor_uuid: str = None) -> Dict[str, Any]:
        """Générer rapport qualité air à partir des données BD"""
        data = self._fetch_air_quality_data(sensor_uuid)
        
        if self.provider != "fallback":
            prompt = f"""Tu es un expert en qualité de l'air urbaine pour la ville de Sousse.
Analyse ces données de capteurs et génère un rapport professionnel en français:

Données capteurs qualité air:
{json.dumps(data, ensure_ascii=False, indent=2, default=str)}

Génère un rapport court (5-8 phrases) incluant:
1. Résumé de l'état de la qualité de l'air
2. Zones préoccupantes si les seuils sont dépassés (PM2.5 > 25µg/m³, PM10 > 50µg/m³, NO2 > 40ppb)
3. Recommandations d'action pour les gestionnaires
4. Tendance générale

Format: Texte structuré avec des sections claires."""
            
            report_text = self._llm_generate(prompt)
            if report_text:
                return {
                    "type": "qualite_air",
                    "timestamp": datetime.now().isoformat(),
                    "provider": self.provider,
                    "model": self.model,
                    "data": data,
                    "report": report_text,
                }

        # Fallback
        return self._fallback_air_report(data)

    def _fetch_air_quality_data(self, sensor_uuid: str = None) -> Dict:
        if not get_db:
            return {"error": "BD non connectée"}
        try:
            db = get_db()
            if sensor_uuid:
                rows = db.fetch_all(
                    "SELECT NomGrandeur, AVG(Valeur) as moy, MAX(Valeur) as max_val, "
                    "MIN(Valeur) as min_val, COUNT(*) as nb "
                    "FROM mesures1 WHERE UUID = %s GROUP BY NomGrandeur",
                    (sensor_uuid,)
                )
            else:
                rows = db.fetch_all(
                    "SELECT m.NomGrandeur, AVG(m.Valeur) as moy, MAX(m.Valeur) as max_val, "
                    "MIN(m.Valeur) as min_val, COUNT(*) as nb "
                    "FROM mesures1 m "
                    "JOIN capteur c ON m.UUID = c.UUID "
                    "WHERE c.Type = 'Qualité de l''air' "
                    "GROUP BY m.NomGrandeur"
                )
            return {"measures": rows if rows else [], "sensor_uuid": sensor_uuid}
        except Exception as e:
            return {"error": str(e)}

    def _fallback_air_report(self, data: Dict) -> Dict:
        measures = data.get("measures", [])
        lines = ["📊 Rapport Qualité de l'Air — Neo-Sousse", f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""]
        
        alerts = []
        for m in measures:
            name = m.get("NomGrandeur", "")
            avg = float(m.get("moy", 0))
            mx = float(m.get("max_val", 0))
            
            if name == "PM2.5" and avg > 25:
                alerts.append(f"⚠️ PM2.5 moyen: {avg:.1f}µg/m³ (seuil: 25)")
            if name == "PM10" and avg > 50:
                alerts.append(f"⚠️ PM10 moyen: {avg:.1f}µg/m³ (seuil: 50)")
            if name == "NO2" and avg > 40:
                alerts.append(f"⚠️ NO2 moyen: {avg:.1f}ppb (seuil: 40)")
            
            lines.append(f"  {name}: moy={avg:.1f}, max={mx:.1f} ({m.get('nb', 0)} mesures)")
        
        if alerts:
            lines.append("\n⚠️ ALERTES:")
            lines.extend(f"  {a}" for a in alerts)
            lines.append("\n💡 Recommandation: Renforcer la surveillance dans les zones à risque.")
        else:
            lines.append("\n✅ Qualité de l'air dans les normes. Aucune action requise.")
        
        return {
            "type": "qualite_air", "timestamp": datetime.now().isoformat(),
            "provider": "fallback", "model": "template",
            "data": data, "report": "\n".join(lines),
        }

    # ═══════════════════════════════════════════════════════════════
    # 2. Suggestion d'Action (Énoncé §2.3.2)
    # ═══════════════════════════════════════════════════════════════

    def suggest_intervention(self, sensor_uuid: str) -> Dict[str, Any]:
        """Suggérer intervention pour un capteur"""
        info = self._fetch_sensor_info(sensor_uuid)
        
        if self.provider != "fallback":
            prompt = f"""Tu es un système expert de maintenance IoT pour une ville intelligente.
Analyse ce capteur et suggère des actions.
RÈGLE STRICTE: SANS AUCUN ASTÉRISQUE, AUCUN GRAS, AUCUN MARKDOWN. Texte brut uniquement. N'utilise jamais les symboles ** dans ta réponse.

{json.dumps(info, ensure_ascii=False, indent=2, default=str)}

Réponds en français avec exactement cette structure en texte brut:
Diagnostic: (1-2 phrases)
Action recommandée: (maintenance préventive, corrective ou aucune)
Priorité: (haute/moyenne/basse)
Coût estimé: (si intervention nécessaire)"""

            text = self._llm_generate(prompt, max_tokens=300)
            if text:
                return {
                    "sensor_uuid": sensor_uuid, "provider": self.provider,
                    "suggestion": text, "timestamp": datetime.now().isoformat(),
                }

        # Fallback
        statut = info.get("statut", "")
        nb = info.get("nb_mesures", 0)
        if statut in ("Hors Service", "En Maintenance", "Signalé"):
            sugg = f"🔴 Capteur {sensor_uuid[:8]}... en état '{statut}'. Intervention corrective recommandée. Priorité: HAUTE."
        elif nb == 0:
            sugg = f"⚠️ Capteur {sensor_uuid[:8]}... aucune mesure enregistrée. Vérification recommandée. Priorité: MOYENNE."
        else:
            sugg = f"✅ Capteur {sensor_uuid[:8]}... fonctionnement normal ({nb} mesures). Aucune action requise."

        return {"sensor_uuid": sensor_uuid, "provider": "fallback", "suggestion": sugg, "timestamp": datetime.now().isoformat()}

    def _fetch_sensor_info(self, uuid: str) -> Dict:
        if not get_db:
            return {}
        try:
            db = get_db()
            sensor = db.fetch_one("SELECT * FROM capteur WHERE UUID = %s", (uuid,))
            count = db.fetch_one("SELECT COUNT(*) as nb FROM mesures1 WHERE UUID = %s", (uuid,))
            return {
                **(sensor or {}),
                "nb_mesures": count.get("nb", 0) if count else 0,
            }
        except Exception as e:
            return {"error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # 3. Validation Intervention par IA (Énoncé §2.3.3 - avancé)
    # ═══════════════════════════════════════════════════════════════

    def validate_intervention(self, intervention_id: int) -> Dict[str, Any]:
        """Valider une intervention et générer diagnostic IA + 3 solutions"""
        info = self._fetch_intervention_info(intervention_id)

        if self.provider != "fallback":
            prompt = f"""Tu es un système IA de validation d'interventions pour la Smart City de Sousse.
Analyse cette intervention et valide si elle peut être marquée comme terminée.
RÈGLE STRICTE: Ton style de rédaction DOIT être purement factuel, assertif et professionnel. N'utilise JAMAIS de formulations interrogatives (pas de questions). Sois direct dans le diagnostic et les solutions.

{json.dumps(info, ensure_ascii=False, indent=2, default=str)}

Réponds en JSON avec:
{{
  "diagnostic": "description factuelle du problème et de l'intervention sans poser de questions",
  "solution_principale": "solution affirmative recommandée",
  "solution_2": "alternative affirmative 1",
  "solution_3": "alternative affirmative 2",
  "confiance": 85,
  "duree_estimee_heures": 1.5,
  "cout_estime": 150.00,
  "validation": true
}}"""
            text = self._llm_generate(prompt, max_tokens=500)
            if text:
                try:
                    # Try to parse JSON from response
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    if start >= 0 and end > start:
                        parsed = json.loads(text[start:end])
                        self._persist_ia_report(intervention_id, parsed)
                        return {"intervention_id": intervention_id, "provider": self.provider, **parsed}
                except json.JSONDecodeError:
                    pass
                return {"intervention_id": intervention_id, "provider": self.provider, "raw_response": text}

        # Fallback
        nature = info.get("Nature", "Corrective")
        result = {
            "intervention_id": intervention_id,
            "provider": "fallback",
            "diagnostic": f"Intervention {nature} pour capteur {info.get('UUID', 'N/A')[:8]}...",
            "solution_principale": "Calibrage et vérification complète du capteur",
            "solution_2": "Remplacement du module défaillant",
            "solution_3": "Mise à jour firmware et reconfiguration",
            "confiance": 75,
            "duree_estimee_heures": float(info.get("Durée", 30)) / 60,
            "cout_estime": float(info.get("Coût", 100)),
            "validation": True,
        }
        self._persist_ia_report(intervention_id, result)
        return result

    def _fallback_intervention_result(self, info: Dict) -> Dict:
        """Generate fallback intervention validation (testable without DB)"""
        nature = info.get("Nature", "Corrective")
        uuid_str = info.get("UUID", "N/A")
        uuid_display = uuid_str[:8] if len(uuid_str) >= 8 else uuid_str
        return {
            "diagnostic": f"Intervention {nature} pour capteur {uuid_display}...",
            "solution_principale": "Calibrage et vérification complète du capteur",
            "solution_2": "Remplacement du module défaillant",
            "solution_3": "Mise à jour firmware et reconfiguration",
            "confiance": 75,
            "duree_estimee_heures": float(info.get("Durée", 30)) / 60,
            "cout_estime": float(info.get("Coût", 100)),
            "validation": True,
        }

    def _fetch_intervention_info(self, idin: int) -> Dict:
        if not get_db:
            return {}
        try:
            db = get_db()
            row = db.fetch_one("SELECT * FROM intervention WHERE IDIn = %s", (idin,))
            return row or {}
        except Exception as e:
            return {"error": str(e)}

    def _persist_ia_report(self, intervention_id: int, data: Dict):
        if not get_db:
            return
        try:
            db = get_db()
            db.execute_query(
                "INSERT INTO rapports_ia "
                "(intervention_id, diagnostic, solution_principale, solution_2, solution_3, "
                "confiance, duree_estimee_heures, cout_estime, llm_provider, model_used) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    intervention_id,
                    data.get("diagnostic", ""),
                    data.get("solution_principale", ""),
                    data.get("solution_2", ""),
                    data.get("solution_3", ""),
                    data.get("confiance", 0),
                    data.get("duree_estimee_heures", 0),
                    data.get("cout_estime", 0),
                    self.provider,
                    self.model,
                )
            )
            logger.info(f"✅ Rapport IA persisté pour intervention {intervention_id}")
        except Exception as e:
            logger.error(f"Erreur persistance rapport IA: {e}")

    # ═══════════════════════════════════════════════════════════════
    # Dashboard summary
    # ═══════════════════════════════════════════════════════════════

    def generate_dashboard_summary(self) -> Dict[str, Any]:
        """Générer un résumé global pour le dashboard"""
        if not get_db:
            return {"report": "Base de données non connectée"}
        try:
            db = get_db()
            stats = {
                "capteurs_total": db.fetch_one("SELECT COUNT(*) as n FROM capteur"),
                "capteurs_actifs": db.fetch_one("SELECT COUNT(*) as n FROM capteur WHERE Statut='Actif'"),
                "capteurs_hs": db.fetch_one("SELECT COUNT(*) as n FROM capteur WHERE Statut='Hors Service'"),
                "interventions_total": db.fetch_one("SELECT COUNT(*) as n FROM intervention"),
                "interventions_terminees": db.fetch_one("SELECT COUNT(*) as n FROM intervention WHERE statut='Terminée'"),
                "vehicules_total": db.fetch_one("SELECT COUNT(*) as n FROM véhicule"),
                "citoyens_total": db.fetch_one("SELECT COUNT(*) as n FROM citoyen"),
                "score_moyen": db.fetch_one("SELECT AVG(Score) as avg_score FROM citoyen"),
            }
            # Extract values
            for k, v in stats.items():
                if isinstance(v, dict):
                    stats[k] = v.get("n", v.get("avg_score", 0))
            
            if self.provider != "fallback":
                prompt = f"""Génère un résumé exécutif en français (4-5 phrases) pour le tableau de bord 
de la Smart City Neo-Sousse basé sur ces statistiques:
{json.dumps(stats, ensure_ascii=False, default=str)}
Mentionne les points clés et les recommandations."""
                text = self._llm_generate(prompt, 300)
                if text:
                    return {"stats": stats, "report": text, "provider": self.provider}
            
            # Fallback
            total = stats.get("capteurs_total", 0) or 0
            actifs = stats.get("capteurs_actifs", 0) or 0
            hs = stats.get("capteurs_hs", 0) or 0
            rate = (actifs / total * 100) if total else 0
            
            report = (
                f"📊 Résumé Neo-Sousse Smart City\n"
                f"• {total} capteurs déployés ({actifs} actifs, taux: {rate:.0f}%)\n"
                f"• {hs} capteurs hors service nécessitant attention\n"
                f"• {stats.get('interventions_total', 0)} interventions enregistrées "
                f"({stats.get('interventions_terminees', 0)} terminées)\n"
                f"• {stats.get('vehicules_total', 0)} véhicules dans le réseau\n"
                f"• Score citoyen moyen: {float(stats.get('score_moyen', 0) or 0):.0f}/100"
            )
            return {"stats": stats, "report": report, "provider": "fallback"}
        except Exception as e:
            return {"report": f"Erreur: {e}", "provider": "error"}

    # ═══════════════════════════════════════════════════════════════
    # 4. Custom Report from Natural Language (§2.3 — User Request)
    # ═══════════════════════════════════════════════════════════════

    def generate_custom_report(self, user_query: str) -> Dict[str, Any]:
        """
        Générer un rapport personnalisé basé sur une demande en langage naturel.
        
        L'utilisateur peut demander n'importe quoi existant dans la base:
          - "Rapport sur les capteurs hors service"
          - "Analyse des interventions du mois"
          - "État des véhicules électriques"
          - "Score d'engagement des citoyens"
          etc.
        """
        # 1. Detect what data to fetch based on the query
        query_lower = user_query.lower()
        data = {}
        report_type = "ANALYSE PERSONNALISÉE"
        title = user_query

        # Fetch relevant data based on keywords
        if any(w in query_lower for w in ['capteur', 'sensor', 'iot', 'qualité', 'air', 'mesure']):
            data['sensors'] = self._fetch_all_sensors()
            data['measures'] = self._fetch_measures_summary()
            report_type = "CAPTEURS IoT"
        
        if any(w in query_lower for w in ['intervention', 'maintenance', 'réparation', 'technicien']):
            data['interventions'] = self._fetch_all_interventions()
            report_type = "INTERVENTIONS" if 'sensors' not in data else report_type
        
        if any(w in query_lower for w in ['véhicule', 'vehicule', 'trajet', 'co2', 'mobilité']):
            data['vehicles'] = self._fetch_all_vehicles()
            data['trips'] = self._fetch_all_trips()
            report_type = "MOBILITÉ & VÉHICULES" if 'sensors' not in data and 'interventions' not in data else report_type
        
        if any(w in query_lower for w in ['citoyen', 'engagement', 'score', 'participation']):
            data['citizens'] = self._fetch_all_citizens()
            report_type = "ENGAGEMENT CITOYEN" if len(data) <= 1 else report_type

        # If no specific match, fetch everything
        if not data:
            data['sensors'] = self._fetch_all_sensors()
            data['interventions'] = self._fetch_all_interventions()
            data['vehicles'] = self._fetch_all_vehicles()
            data['trips'] = self._fetch_all_trips()
            data['citizens'] = self._fetch_all_citizens()
            report_type = "RAPPORT GLOBAL"

        # 2. Generate IA analysis
        if self.provider != "fallback":
            data_summary = {}
            for k, v in data.items():
                if isinstance(v, list):
                    data_summary[f"{k}_total"] = len(v)
                    # Envoyer seulement un petit échantillon (max 3) pour éviter l'engorgement du LLM local (Ollama freeze)
                    data_summary[f"{k}_examples"] = v[:3]
                    # Pre-compute stats for common fields
                    if k == 'sensors' and v:
                        statut_counts = {}
                        type_counts = {}
                        for s in v:
                            st = s.get('Statut', 'N/A')
                            statut_counts[st] = statut_counts.get(st, 0) + 1
                            tp = s.get('Type', 'N/A')
                            type_counts[tp] = type_counts.get(tp, 0) + 1
                        data_summary['sensors_par_statut'] = statut_counts
                        data_summary['sensors_par_type'] = type_counts
                    if k == 'interventions' and v:
                        st_counts = {}
                        for i in v:
                            st = i.get('statut', 'N/A')
                            st_counts[st] = st_counts.get(st, 0) + 1
                        data_summary['interventions_par_statut'] = st_counts
                    if k == 'vehicles' and v:
                        en_counts = {}
                        for veh in v:
                            e = veh.get('Énergie Utilisée', 'N/A')
                            en_counts[e] = en_counts.get(e, 0) + 1
                        data_summary['vehicules_par_energie'] = en_counts
                else:
                    data_summary[k] = v

            prompt = f"""Tu es un analyste de données pour la Smart City Neo-Sousse 2030.
L'utilisateur demande: "{user_query}"

RÈGLES STRICTES:
- Utilise UNIQUEMENT les données ci-dessous. Ne fabrique AUCUN chiffre.
- Ne mentionne AUCUNE information qui ne figure pas dans les données fournies.
- Si une donnée n'est pas disponible, dis-le clairement.
- Les chiffres dans ton rapport doivent correspondre EXACTEMENT aux données ci-dessous.

DONNÉES RÉELLES DE LA BASE DE DONNÉES:
{json.dumps(data_summary, ensure_ascii=False, indent=2, default=str)}

Génère un rapport structuré en français avec:
1. Résumé (2-3 phrases basées UNIQUEMENT sur les données ci-dessus)
2. Détails des données (chiffres exacts tirés des données fournies)
3. Recommandations (2-3 points concrets)

IMPORTANT: Ne parle que de ce qui existe dans les données fournies."""

            report_text = self._llm_generate(prompt, max_tokens=800)
            if report_text:
                return {
                    "type": "custom",
                    "query": user_query,
                    "report_type": report_type,
                    "title": title,
                    "timestamp": datetime.now().isoformat(),
                    "provider": self.provider,
                    "model": self.model,
                    "data": data,
                    "report": report_text,
                }

        # 3. Fallback: Generate structured report without LLM
        return self._fallback_custom_report(user_query, report_type, data)

    def _fallback_custom_report(self, query: str, report_type: str, data: Dict) -> Dict:
        """Generate a structured report without LLM"""
        lines = [
            f"📋 RAPPORT: {query}",
            f"📅 Date: {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            f"📁 Type: {report_type}",
            "",
            "═" * 50,
            "📊 RÉSUMÉ EXÉCUTIF",
            "═" * 50,
            "",
        ]

        # Sensors summary
        if 'sensors' in data:
            sensors = data['sensors']
            total = len(sensors)
            actifs = len([s for s in sensors if s.get('Statut') == 'Actif'])
            hs = len([s for s in sensors if s.get('Statut') == 'Hors Service'])
            maint = len([s for s in sensors if s.get('Statut') == 'En Maintenance'])
            rate = (actifs / total * 100) if total > 0 else 0

            lines.extend([
                "📡 CAPTEURS IoT",
                f"  • Total déployés: {total}",
                f"  • Actifs: {actifs} ({rate:.0f}%)",
                f"  • En maintenance: {maint}",
                f"  • Hors service: {hs}",
            ])
            if hs > 0:
                lines.append(f"  ⚠️ ALERTE: {hs} capteurs hors service nécessitent intervention immédiate")
            
            # Type breakdown
            types = {}
            for s in sensors:
                t = s.get('Type', 'N/A')
                types[t] = types.get(t, 0) + 1
            lines.append("  Types:")
            for t, c in types.items():
                lines.append(f"    - {t}: {c}")
            lines.append("")

        # Interventions summary
        if 'interventions' in data:
            interventions = data['interventions']
            total_i = len(interventions)
            terminées = len([i for i in interventions if i.get('statut') == 'Terminée'])
            
            lines.extend([
                "🔧 INTERVENTIONS",
                f"  • Total: {total_i}",
                f"  • Terminées: {terminées}",
                f"  • En cours: {total_i - terminées}",
            ])
            natures = {}
            for i in interventions:
                n = i.get('Nature', 'N/A')
                natures[n] = natures.get(n, 0) + 1
            for n, c in natures.items():
                lines.append(f"    - {n}: {c}")
            lines.append("")

        # Vehicles summary
        if 'vehicles' in data:
            vehicles = data['vehicles']
            trips = data.get('trips', [])
            co2 = sum(float(t.get('ÉconomieCO2', 0) or 0) for t in trips)
            
            lines.extend([
                "🚗 VÉHICULES & MOBILITÉ",
                f"  • Véhicules: {len(vehicles)}",
                f"  • Trajets: {len(trips)}",
                f"  • CO₂ économisé: {co2:.1f} kg",
            ])
            energies = {}
            for v in vehicles:
                e = v.get('Énergie Utilisée', 'N/A')
                energies[e] = energies.get(e, 0) + 1
            for e, c in energies.items():
                lines.append(f"    - {e}: {c}")
            lines.append("")

        # Citizens summary
        if 'citizens' in data:
            citizens = data['citizens']
            avg = sum(c.get('Score', 0) or 0 for c in citizens) / max(len(citizens), 1)
            lines.extend([
                "👥 CITOYENS",
                f"  • Total: {len(citizens)}",
                f"  • Score moyen: {avg:.0f}/100",
            ])
            lines.append("")

        # Recommendations
        lines.extend([
            "═" * 50,
            "💡 RECOMMANDATIONS",
            "═" * 50,
        ])
        
        if 'sensors' in data:
            hs_count = len([s for s in data['sensors'] if s.get('Statut') == 'Hors Service'])
            if hs_count > 0:
                lines.append(f"  1. Planifier {hs_count} intervention(s) corrective(s) pour les capteurs hors service")
            lines.append("  2. Renforcer la maintenance préventive pour réduire les pannes")
        if 'interventions' in data:
            en_cours = len([i for i in data['interventions'] if i.get('statut') != 'Terminée'])
            if en_cours > 0:
                lines.append(f"  3. Accélérer le traitement des {en_cours} intervention(s) en cours")
        lines.append("  4. Continuer le suivi des indicateurs de performance")
        lines.append("  5. Optimiser l'allocation des ressources techniques")

        lines.extend(["", f"— Rapport généré par IA (mode fallback) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"])

        return {
            "type": "custom",
            "query": query,
            "report_type": report_type,
            "title": query,
            "timestamp": datetime.now().isoformat(),
            "provider": "fallback",
            "model": "template",
            "data": data,
            "report": "\n".join(lines),
        }

    # ═══════════════════════════════════════════════════════════════
    # Data Fetchers for Custom Reports
    # ═══════════════════════════════════════════════════════════════

    def _fetch_all_sensors(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all("SELECT * FROM Capteur") or []
        except: return []

    def _fetch_measures_summary(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all(
                "SELECT NomGrandeur, AVG(Valeur) as moy, MAX(Valeur) as max_val, "
                "MIN(Valeur) as min_val, COUNT(*) as nb FROM Mesures1 GROUP BY NomGrandeur"
            ) or []
        except: return []

    def _fetch_all_interventions(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all(
                "SELECT i.*, t1.Nom as tech1_name, t2.Nom as tech2_name "
                "FROM Intervention i "
                "LEFT JOIN Technicien t1 ON i.technicien_1_id = t1.IDT "
                "LEFT JOIN Technicien t2 ON i.technicien_2_id = t2.IDT "
                "ORDER BY i.DateHeure DESC"
            ) or []
        except: return []

    def _fetch_all_vehicles(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all("SELECT * FROM `Véhicule`") or []
        except: return []

    def _fetch_all_trips(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all("SELECT * FROM Trajet ORDER BY Date DESC") or []
        except: return []

    def _fetch_all_citizens(self) -> List[Dict]:
        if not get_db: return []
        try:
            db = get_db()
            return db.fetch_all("SELECT * FROM Citoyen ORDER BY Score DESC") or []
        except: return []
