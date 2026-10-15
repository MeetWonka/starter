#!/usr/bin/env python3
"""Build the "Model comparison" help page from the WonkaChat model config.

Two steps, like scripts/integrations/build.py:

  sync      Read the models offered in the model picker from the Config repo
            (prod values: endpoints.custom[].modelCategories) and write
            models.json. Needs a local clone of the Config repo.

  generate  Write <lang>/improved-usage/model-comparison.mdx for en, fr and nl
            from models.json + catalog.yaml. Offline.

Usage:
  python3 scripts/models/build.py sync --config ../Config
  python3 scripts/models/build.py generate

Costs are shown as relative tiers (€ to €€€€), never as prices: exact prices
live on wonka-ai.com/pricing. Benchmarks come from one public source, recorded
with its date in catalog.yaml.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MODELS_JSON = HERE / "models.json"
CATALOG_YAML = HERE / "catalog.yaml"
PAGE_SLUG = "improved-usage/model-comparison"
LANGS = ("en", "fr", "nl")


# --------------------------------------------------------------------------- sync


def sync(args) -> None:
    config_repo = Path(args.config).expanduser().resolve()
    if args.fetch:
        subprocess.run(["git", "-C", str(config_repo), "fetch", "-q", "origin", "main"], check=True)
    values = subprocess.run(
        ["git", "-C", str(config_repo), "show", f"{args.ref}:wonkachat/prod/values.yaml"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    cfg = yaml.safe_load(yaml.safe_load(values)["librechat"]["configYamlContent"])

    out = {}
    for endpoint in cfg["endpoints"]["custom"]:
        names = endpoint.get("modelDisplayNames") or {}
        categories = endpoint.get("modelCategories") or {}
        tokens = endpoint.get("tokenConfig") or {}
        for model in endpoint["models"]["default"]:
            cat = categories.get(model) or {}
            # Same rule as the model picker: only models not marked selectable: false.
            if cat.get("selectable") is False:
                continue
            out[model] = {
                "name": names.get(model, model),
                "endpoint": endpoint["name"],
                "description": cat.get("description", ""),
                "region": cat.get("region", "global"),
                "cost": cat.get("cost"),
                "speed": cat.get("speedScore"),
                "intelligence": cat.get("intelligenceScore"),
                "reasoning": bool(cat.get("reasoning")),
                "featured": bool(cat.get("featured")),
                "featuredOrder": cat.get("featuredOrder"),
                "context": (tokens.get(model) or {}).get("context"),
            }

    MODELS_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} models to {MODELS_JSON.relative_to(ROOT)}")


# ----------------------------------------------------------------------- generate

T = {
    "en": {
        "title": "Model comparison",
        "description": "Every model in WonkaChat side by side: what it is best at, speed, cost, region and public benchmarks.",
        "intro": (
            "WonkaChat gives you {count} AI models from {providers} providers. This page helps you pick one: "
            "start with the task you have in mind, then compare the models in detail."
        ),
        "not_sure": (
            "Not sure? Pick the **Router** in the model picker: it chooses a model for each message. "
            "See [Choosing a model](/en/improved-usage/choosing-a-model)."
        ),
        "tasks_title": "Which model for which task",
        "tasks_head": "| Task | Recommended models |",
        "featured_title": "Recommended models",
        "featured_body": "These models are highlighted in the model picker. They cover most needs.",
        "all_title": "All models",
        "all_head": "| Model | Provider | Best for | Speed | Cost | Region |",
        "bench_title": "Benchmarks and technical details",
        "bench_body": (
            "**{label}** comes from [{source}]({url}), retrieved on {date}. A higher score is better. "
            "It measures general capability on public tests, not how well a model works with your own tools and data."
        ),
        "bench_head": "| Model | {label} | Reasoning | Context window |",
        "bench_missing": "not rated",
        "reasoning_yes": "Yes",
        "reasoning_no": "No",
        "legend_title": "How to read this page",
        "legend": [
            "**Speed**: how fast the model answers, from ● (slow) to ●●●●● (very fast).",
            "**Cost**: how many credits the model uses compared with the others, from € (lowest) to €€€€ (highest). "
            "See [AI usage and credits](/en/pricing/tokens-guide) for how credits work.",
            "**Region**: where the model runs. 🇪🇺 EU stays in the European Union, 🇺🇸 US runs in the United States, "
            "🌐 Global can run in any region of the provider.",
            "**Reasoning**: the model thinks step by step before answering. Needed for connected business tools (ERP, CRM, email).",
            "**Context window**: how much text the model can read at once (1M tokens is roughly 750,000 words).",
        ],
        "admin_note": (
            "Your administrator decides which models your organization can use. "
            "If a model listed here is missing from your model picker, ask them."
        ),
        "regions": {"eu": "🇪🇺 EU", "us": "🇺🇸 US", "global": "🌐 Global"},
        "updated": "Model list updated on {date}.",
    },
    "fr": {
        "title": "Comparatif des modèles",
        "description": "Tous les modèles de WonkaChat côte à côte : points forts, vitesse, coût, région et benchmarks publics.",
        "intro": (
            "WonkaChat vous donne accès à {count} modèles IA de {providers} fournisseurs. Cette page vous aide à choisir : "
            "partez de votre tâche, puis comparez les modèles en détail."
        ),
        "not_sure": (
            "Vous hésitez ? Choisissez le **Routeur** dans le sélecteur de modèle : il choisit un modèle pour chaque message. "
            "Voir [Choisir un modèle](/fr/improved-usage/choosing-a-model)."
        ),
        "tasks_title": "Quel modèle pour quelle tâche",
        "tasks_head": "| Tâche | Modèles recommandés |",
        "featured_title": "Modèles recommandés",
        "featured_body": "Ces modèles sont mis en avant dans le sélecteur de modèle. Ils couvrent la plupart des besoins.",
        "all_title": "Tous les modèles",
        "all_head": "| Modèle | Fournisseur | Idéal pour | Vitesse | Coût | Région |",
        "bench_title": "Benchmarks et détails techniques",
        "bench_body": (
            "**{label}** provient de [{source}]({url}), relevé le {date}. Plus le score est élevé, mieux c'est. "
            "Il mesure la capacité générale sur des tests publics, pas la qualité du modèle avec vos propres outils et données."
        ),
        "bench_head": "| Modèle | {label} | Raisonnement | Fenêtre de contexte |",
        "bench_missing": "non noté",
        "reasoning_yes": "Oui",
        "reasoning_no": "Non",
        "legend_title": "Comment lire cette page",
        "legend": [
            "**Vitesse** : rapidité de réponse du modèle, de ● (lent) à ●●●●● (très rapide).",
            "**Coût** : crédits consommés par rapport aux autres modèles, de € (le moins cher) à €€€€ (le plus cher). "
            "Voir [Usage IA et crédits](/fr/pricing/tokens-guide) pour le fonctionnement des crédits.",
            "**Région** : où le modèle s'exécute. 🇪🇺 UE reste dans l'Union européenne, 🇺🇸 US s'exécute aux États-Unis, "
            "🌐 Global peut s'exécuter dans n'importe quelle région du fournisseur.",
            "**Raisonnement** : le modèle réfléchit étape par étape avant de répondre. Nécessaire pour les outils métier connectés (ERP, CRM, e-mail).",
            "**Fenêtre de contexte** : quantité de texte que le modèle peut lire d'un coup (1M de tokens représente environ 700 000 mots).",
        ],
        "admin_note": (
            "Votre administrateur décide quels modèles votre organisation peut utiliser. "
            "Si un modèle listé ici n'apparaît pas dans votre sélecteur, demandez-lui."
        ),
        "regions": {"eu": "🇪🇺 UE", "us": "🇺🇸 US", "global": "🌐 Global"},
        "updated": "Liste des modèles mise à jour le {date}.",
    },
    "nl": {
        "title": "Modellen vergelijken",
        "description": "Alle modellen in WonkaChat naast elkaar: sterke punten, snelheid, kosten, regio en publieke benchmarks.",
        "intro": (
            "WonkaChat geeft u toegang tot {count} AI-modellen van {providers} aanbieders. Deze pagina helpt u kiezen: "
            "begin bij uw taak en vergelijk daarna de modellen in detail."
        ),
        "not_sure": (
            "Twijfelt u? Kies de **Router** in de modelkiezer: die kiest per bericht een model. "
            "Zie [Een model kiezen](/nl/improved-usage/choosing-a-model)."
        ),
        "tasks_title": "Welk model voor welke taak",
        "tasks_head": "| Taak | Aanbevolen modellen |",
        "featured_title": "Aanbevolen modellen",
        "featured_body": "Deze modellen worden uitgelicht in de modelkiezer. Ze dekken de meeste behoeften.",
        "all_title": "Alle modellen",
        "all_head": "| Model | Aanbieder | Ideaal voor | Snelheid | Kosten | Regio |",
        "bench_title": "Benchmarks en technische details",
        "bench_body": (
            "**{label}** komt van [{source}]({url}), opgehaald op {date}. Hoe hoger de score, hoe beter. "
            "De score meet algemene capaciteit op publieke tests, niet hoe goed een model werkt met uw eigen tools en gegevens."
        ),
        "bench_head": "| Model | {label} | Redeneren | Contextvenster |",
        "bench_missing": "niet beoordeeld",
        "reasoning_yes": "Ja",
        "reasoning_no": "Nee",
        "legend_title": "Hoe leest u deze pagina",
        "legend": [
            "**Snelheid**: hoe snel het model antwoordt, van ● (traag) tot ●●●●● (zeer snel).",
            "**Kosten**: hoeveel credits het model verbruikt ten opzichte van de andere, van € (laagst) tot €€€€ (hoogst). "
            "Zie [AI-gebruik en credits](/nl/pricing/tokens-guide) voor hoe credits werken.",
            "**Regio**: waar het model draait. 🇪🇺 EU blijft in de Europese Unie, 🇺🇸 VS draait in de Verenigde Staten, "
            "🌐 Globaal kan in elke regio van de aanbieder draaien.",
            "**Redeneren**: het model denkt stap voor stap na voor het antwoordt. Nodig voor verbonden bedrijfstools (ERP, CRM, e-mail).",
            "**Contextvenster**: hoeveel tekst het model in één keer kan lezen (1M tokens is ongeveer 750.000 woorden).",
        ],
        "admin_note": (
            "Uw beheerder bepaalt welke modellen uw organisatie kan gebruiken. "
            "Ontbreekt een model uit deze lijst in uw modelkiezer, vraag het dan aan uw beheerder."
        ),
        "regions": {"eu": "🇪🇺 EU", "us": "🇺🇸 VS", "global": "🌐 Globaal"},
        "updated": "Modellenlijst bijgewerkt op {date}.",
    },
}


MONTHS = {
    "en": "January February March April May June July August September October November December",
    "fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre",
    "nl": "januari februari maart april mei juni juli augustus september oktober november december",
}


def day(d, lang: str) -> str:
    """Localized date: October 15, 2026 / 15 octobre 2026 / 15 oktober 2026."""
    month = MONTHS[lang].split()[d.month - 1]
    if lang == "en":
        return f"{month} {d.day}, {d.year}"
    num = "1er" if lang == "fr" and d.day == 1 else d.day
    return f"{num} {month} {d.year}"


def dots(n) -> str:
    return "●" * n + "○" * (5 - n) if n else "—"


def euros(n) -> str:
    return "€" * n if n else "—"


def context(tokens) -> str:
    if not tokens:
        return "—"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.0f}M tokens"
    return f"{tokens // 1000}K tokens"


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def tr(value, lang: str, what: str) -> str:
    """Pick the translation for lang from a {en, fr, nl} dict, warning on fallback."""
    if isinstance(value, str):
        return value
    if lang in value:
        return value[lang]
    print(f"WARNING: no {lang} text for {what}, using English", file=sys.stderr)
    return value["en"]


def render(lang: str, models: dict, catalog: dict, updated: str) -> str:
    t = T[lang]
    providers = catalog["providers"]
    descriptions = catalog.get("descriptions") or {}
    bench = catalog.get("benchmark") or {}
    scores = bench.get("scores") or {}

    def desc(key):
        d = descriptions.get(key)
        if d is None:
            print(f"WARNING: no description override for '{key}', using the config text", file=sys.stderr)
            return models[key]["description"]
        return tr(d, lang, f"description of {key}")

    def link(key):
        return f"[{models[key]['name']}](#{anchor(models[key]['name'])})"

    ordered = sorted(
        models,
        key=lambda k: (
            not models[k]["featured"],
            models[k]["featuredOrder"] or 99,
            providers[models[k]["endpoint"]],
            models[k]["name"],
        ),
    )
    featured = [k for k in ordered if models[k]["featured"]]

    out = [
        "---",
        f'title: "{t["title"]}"',
        f'description: "{t["description"]}"',
        "---",
        "",
        "{/* Generated by scripts/models/build.py. Do not edit by hand: edit catalog.yaml or the script, then run `build.py generate`. */}",
        "",
        t["intro"].format(count=len(models), providers=len({models[k]["endpoint"] for k in models})),
        "",
        f"<Tip>{t['not_sure']}</Tip>",
        "",
        f"## {t['tasks_title']}",
        "",
        t["tasks_head"],
        "|---|---|",
    ]
    for task in catalog["tasks"]:
        picks = [k for k in task["models"] if k in models]
        missing = [k for k in task["models"] if k not in models]
        if missing:
            print(f"WARNING: task '{task['id']}' recommends models not offered: {missing}", file=sys.stderr)
        out.append(f"| {cell(tr(task['label'], lang, 'task ' + task['id']))} | {', '.join(link(k) for k in picks)} |")

    out += ["", f"## {t['featured_title']}", "", t["featured_body"], "", "<CardGroup cols={2}>"]
    for k in featured:
        m = models[k]
        meta = f"{providers[m['endpoint']]} · {euros(m['cost'])} · {t['regions'][m['region']]}"
        out += [f'<Card title="{m["name"]}">', f"{meta}", "", desc(k), "</Card>"]
    out += ["</CardGroup>", ""]

    out += [f"## {t['all_title']}", "", t["all_head"], "|---|---|---|---|---|---|"]
    for k in ordered:
        m = models[k]
        out.append(
            f'| <a id="{anchor(m["name"])}"></a>**{cell(m["name"])}** | {providers[m["endpoint"]]} | {cell(desc(k))} '
            f"| {dots(m['speed'])} | {euros(m['cost'])} | {t['regions'][m['region']]} |"
        )
    out.append("")

    if bench:
        label = tr(bench["label"], lang, "benchmark label")
        out += [
            f"## {t['bench_title']}",
            "",
            t["bench_body"].format(label=label, source=bench["source"], url=bench["url"], date=day(bench["retrieved"], lang)),
            "",
            t["bench_head"].format(label=label),
            "|---|---|---|---|",
        ]
        by_score = sorted(ordered, key=lambda k: -(scores.get(k) or -1))
        for k in by_score:
            m = models[k]
            score = scores.get(k)
            out.append(
                f"| **{cell(m['name'])}** | {score if score is not None else t['bench_missing']} "
                f"| {t['reasoning_yes'] if m['reasoning'] else t['reasoning_no']} | {context(m['context'])} |"
            )
        out.append("")

    out += [f"## {t['legend_title']}", ""]
    out += [f"- {line}" for line in t["legend"]]
    out += ["", f"<Info>{t['admin_note']}</Info>", "", f"_{t['updated'].format(date=day(updated, lang))}_", ""]
    return "\n".join(out)


def anchor(name: str) -> str:
    return "model-" + "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def generate(_args) -> None:
    models = json.loads(MODELS_JSON.read_text())
    catalog = yaml.safe_load(CATALOG_YAML.read_text())
    hidden = set(catalog.get("hidden") or [])
    models = {k: v for k, v in models.items() if k not in hidden}
    for k, m in models.items():
        if m["endpoint"] not in catalog["providers"]:
            sys.exit(f"Unknown endpoint '{m['endpoint']}' for '{k}': add it to providers in catalog.yaml")
    updated = catalog["updated"]
    for lang in LANGS:
        path = ROOT / lang / f"{PAGE_SLUG}.mdx"
        path.write_text(render(lang, models, catalog, updated))
        print(f"Wrote {path.relative_to(ROOT)} ({len(models)} models)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_sync = sub.add_parser("sync", help="refresh models.json from the Config repo")
    p_sync.add_argument("--config", required=True, help="path to a local clone of the Config repo")
    p_sync.add_argument("--ref", default="origin/main", help="git ref of the Config repo to read")
    p_sync.add_argument("--no-fetch", dest="fetch", action="store_false", help="skip git fetch")
    p_sync.set_defaults(func=sync)
    p_gen = sub.add_parser("generate", help="write the MDX pages from models.json")
    p_gen.set_defaults(func=generate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
