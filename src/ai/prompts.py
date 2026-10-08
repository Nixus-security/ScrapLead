INTENT_ANALYSIS_PROMPT = """Analyse ce commentaire/post pour déterminer l'intention d'achat du user.

Plateforme: {platform}
Texte: {text}

Donne un score de 0 à 100:
- 0-30: Pas intéressé, juste curiosité
- 31-60: Intéressé mais pas urgent
- 61-80: Besoin clair, prêt à explorer
- 81-100: Besoin urgent, prêt à acheter MAINTENANT

Réponds UNIQUEMENT en JSON valide:
{{"score": <int>, "reason": "<string court>"}}"""

OUTREACH_EMAIL_TEMPLATE = """Subject: Re: {context}

Hey {first_name},

J'ai vu ton post sur {platform} où tu mentionnais "{snippet}".

{personalized_hook}

Je peux t'aider avec ça. On en parle 10 min ?

{sender_name}"""