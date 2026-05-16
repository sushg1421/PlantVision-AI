import anthropic

client = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")

def get_plant_analysis(scientific_name: str, description: str):
    prompt = f"""
    Plant: {scientific_name}
    Description: {description}

    Please provide:
    1. Medicinal uses
    2. Culinary uses
    3. Toxicity warnings
    4. Plant health tips
    Keep each section brief and factual.
    """

    message = client.messages.create(
        model      = "claude-opus-4-6",
        max_tokens = 1024,
        messages   = [{"role": "user", "content": prompt}]
    )

    return message.content[0].text