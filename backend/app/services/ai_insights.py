def _money(value: float | int | None) -> str:
    return f"R$ {float(value or 0):,.0f}".replace(',', '.')


def build_insights(vehicle: dict, valuation: dict) -> dict:
    name = f"{vehicle['brand']} {vehicle['model']} {vehicle.get('version','')}".strip()
    below_avg = vehicle['km'] < max(10000, (2026 - vehicle['year']) * 12000)
    liquidity = valuation.get('demand_index') or valuation.get('liquidity_score', 0)
    strategy = valuation.get('selling_strategy') or {}
    positioning = valuation.get('price_positioning') or {}
    market_insights = valuation.get('market_insights') or {}
    buyer_insights = valuation.get('buyer_behavior_insights') or []
    safe_range = valuation.get('safe_price_range') or strategy.get('safe_price_range') or valuation.get('negotiation_range') or []

    strengths = []
    if below_avg:
        strengths.append("quilometragem abaixo da média estimada")
    if liquidity >= 85:
        strengths.append("liquidez elevada para revenda")
    elif liquidity >= 68:
        strengths.append("boa leitura de demanda regional")
    if vehicle.get('condition','bom').lower() == 'excelente':
        strengths.append("estado declarado excelente")
    if valuation.get('comparables_used', 0) >= 8:
        strengths.append("boa base de comparáveis para defender o valor")
    if valuation.get('market_position_percentile') and valuation.get('market_position_percentile') <= 45:
        strengths.append("posicionamento competitivo frente aos anúncios comparáveis")
    if not strengths:
        strengths.append("perfil equilibrado para negociação")

    attention = []
    if vehicle['km'] > max(20000, (2026 - vehicle['year']) * 15000):
        attention.append("quilometragem acima da média pode exigir margem de negociação")
    if valuation.get('overvaluation_risk', 0) >= 65:
        attention.append("preço acima do teto provável pode reduzir a liquidez")
    if valuation.get('market_delta_vs_fipe_pct', 0) < -3:
        attention.append("mercado de referência abaixo da FIPE; o teto da faixa pode exigir mais tempo de venda")
    if valuation.get('confidence_level') == 'Baixa':
        attention.append("amostra limitada; recomendável revisar comparáveis antes de anunciar")
    if not attention:
        attention.append("manter fotos boas e histórico de revisão aumenta percepção de valor")

    listing_price = valuation.get('recommended_listing_price') or strategy.get('recommended_listing_price') or valuation.get('ideal_price')
    quick = valuation.get('quick_sale_price') or valuation.get('negotiation_intelligence', {}).get('quick_sale_price')
    safe_low = safe_range[0] if len(safe_range) > 0 else valuation.get('negotiation_range', [quick])[0]
    safe_high = safe_range[1] if len(safe_range) > 1 else valuation.get('negotiation_ceiling') or valuation.get('recommended_top_price')
    executive = valuation.get('executive_market_insight_v2') or valuation.get('executive_market_insight')
    buyer_copy = buyer_insights[0] if buyer_insights else "compradores tendem a comparar preço, km, histórico e praça antes de avançar."

    return {
        "summary": executive or f"O {name} apresenta Índice Meu Carro Vale {valuation['vehicle_score']}/100, valor indicado de {_money(valuation['ideal_price'])} e leitura de mercado {valuation.get('market_temperature_label', valuation.get('market_temperature', 'estável')).lower()}.",
        "analysis": f"A leitura combina FIPE, comparáveis, região, liquidez, comportamento comprador e pressão de preço. Para {vehicle['city']}/{vehicle['state']}, a estratégia recomendada é anunciar em torno de {_money(listing_price)} e acompanhar a resposta nos primeiros dias.",
        "strengths": strengths,
        "attention_points": attention,
        "pricing_recommendation": f"Use a faixa segura entre {_money(safe_low)} e {_money(safe_high)}. Para vender rápido, trabalhe próximo de {_money(quick)}; para defender margem, mantenha o anúncio próximo de {_money(listing_price)} com histórico e fotos bem organizados.",
        "negotiation_recommendation": f"{buyer_copy} Evite desconto inicial alto; use comparáveis e liquidez como argumento objetivo.",
        "market_perception": market_insights.get('market_thesis') or positioning.get('positioning_summary') or "Preço coerente, descrição clara e histórico organizado aumentam a qualidade dos contatos."
    }


def build_ads(vehicle: dict, valuation: dict) -> dict:
    name = f"{vehicle['brand']} {vehicle['model']} {vehicle.get('version','')} {vehicle['year']}".strip()
    base = f"{name}, {vehicle['transmission']}, {vehicle['fuel']}, {vehicle['km']:,} km".replace(',', '.')
    listing_price = valuation.get('recommended_listing_price') or valuation.get('ideal_price')
    quick = valuation.get('quick_sale_price')
    market_note = valuation.get('market_temperature_label') or valuation.get('market_temperature') or 'estável'
    return {
        "title": f"{name} — valor alinhado ao mercado e pronto para negociar",
        "description": f"{base}. Veículo com análise Meu Carro Vale considerando FIPE, comparáveis, região, liquidez e posicionamento de preço. Preço recomendado para anúncio: {_money(listing_price)}. Venda rápida estimada próxima de {_money(quick)}. Mercado atual: {market_note}.",
        "olx": f"Vendo {base}. Preço baseado em comparáveis da região e faixa de negociação transparente. Chamar para mais detalhes.",
        "webmotors": f"{name} em boa apresentação. Laudo Meu Carro Vale indica preço recomendado de {_money(listing_price)} e faixa de negociação sustentada por comparáveis e liquidez.",
        "marketplace": f"{name} disponível. Preço alinhado ao mercado, com leitura de liquidez e comparáveis. Aberto a proposta consciente."
    }
