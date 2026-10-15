#!/usr/bin/env python3
"""Build the "All integrations" help page from the WonkaChat connector config.

Two steps, so the docs never need access to secrets or other repos to build:

  sync      Read the connectors from the Config repo (prod values) and the auth
            scheme of each Composio connector, then write servers.json.
            Needs a local clone of the Config repo and the `composio` CLI logged
            in to the WonkaChat Composio project.

  generate  Write <lang>/tools-connection/integrations-catalog.mdx for en, fr
            and nl from servers.json + catalog.yaml. Offline, no credentials.

Usage:
  python3 scripts/integrations/build.py sync --config ../Config
  python3 scripts/integrations/build.py generate
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SERVERS_JSON = HERE / "servers.json"
CATALOG_YAML = HERE / "catalog.yaml"
PAGE_SLUG = "tools-connection/integrations-catalog"
LANGS = ("en", "fr", "nl")
MODES = ("oauth", "api_key", "credentials", "assisted")


# --------------------------------------------------------------------------- sync


def load_prod_servers(config_repo: Path, ref: str) -> dict:
    values = subprocess.run(
        ["git", "-C", str(config_repo), "show", f"{ref}:wonkachat/prod/values.yaml"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    librechat_yaml = yaml.safe_load(values)["librechat"]["configYamlContent"]
    return yaml.safe_load(librechat_yaml)["mcpServers"]


def load_composio_schemes() -> dict:
    out = subprocess.run(
        ["composio", "dev", "auth-configs", "list", "--limit", "1000"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    data = json.loads(out)
    items = data if isinstance(data, list) else data.get("items", [])
    return {item["id"]: item.get("auth_scheme") for item in items}


def sync(args) -> None:
    config_repo = Path(args.config).expanduser().resolve()
    if args.fetch:
        subprocess.run(["git", "-C", str(config_repo), "fetch", "-q", "origin", "main"], check=True)
    servers = load_prod_servers(config_repo, args.ref)
    schemes = load_composio_schemes()

    out = {}
    missing = []
    for key, cfg in sorted(servers.items()):
        provider = cfg.get("provider") or "direct"
        entry = {
            "provider": provider,
            "description": cfg.get("description", ""),
            "iconURL": cfg.get("iconURL", ""),
            "requiresOAuth": bool(cfg.get("requiresOAuth")),
            "legacy": provider != "composio" and not cfg.get("newVersion"),
            "serverSideHeaders": any("${" in str(v) for v in (cfg.get("headers") or {}).values()),
            "userFields": [
                {"key": k, "title": v.get("title", k), "description": v.get("description", "")}
                for k, v in (cfg.get("customUserVars") or {}).items()
            ],
        }
        if provider == "composio":
            scheme = schemes.get(cfg.get("authConfigId"))
            if not scheme:
                missing.append(key)
            entry["authScheme"] = scheme
        out[key] = entry

    SERVERS_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} connectors to {SERVERS_JSON.relative_to(ROOT)}")
    if missing:
        print(f"WARNING: no Composio auth config found for: {', '.join(missing)}", file=sys.stderr)


# ----------------------------------------------------------------------- generate


def connection_mode(key: str, entry: dict, overrides: dict) -> str:
    if key in overrides:
        return overrides[key]
    if entry["provider"] == "composio":
        return "api_key" if entry.get("authScheme") == "API_KEY" else "oauth"
    if entry["userFields"]:
        return "credentials"
    if entry["requiresOAuth"]:
        return "oauth"
    return "assisted"


def family(key: str) -> str:
    """Server key without its generation suffix: slack_v2 -> slack."""
    return re.sub(r"_v\d+$", "", key)


def display_name(key: str, names: dict) -> str:
    if key in names:
        return names[key]
    print(f"WARNING: no display name for '{key}', add it to catalog.yaml", file=sys.stderr)
    return family(key).replace("_", " ").title()


# Labels of the customUserVars fields used by Wonka-hosted connectors.
FIELD_LABELS = {
    "fr": {
        "Odoo URL": "URL Odoo",
        "Database": "Base de données",
        "Username": "Nom d'utilisateur",
        "Password": "Mot de passe (ou clé API Odoo)",
        "Account ID": "Identifiant de compte (Account ID)",
        "API Key": "Clé API",
        "Client ID": "Client ID",
        "Client Secret": "Client Secret",
    },
    "nl": {
        "Odoo URL": "Odoo-URL",
        "Database": "Database",
        "Username": "Gebruikersnaam",
        "Password": "Wachtwoord (of Odoo API-sleutel)",
        "Account ID": "Account-ID",
        "API Key": "API-sleutel",
        "Client ID": "Client ID",
        "Client Secret": "Client Secret",
    },
    "en": {"Password": "Password (or Odoo API key)"},
}

T = {
    "en": {
        "title": "All integrations",
        "description": "Every connector available in WonkaChat and how to connect it, in one page.",
        "intro": (
            "WonkaChat has more than {count} ready-to-use integrations. They all live in "
            "**Customize → Connectors**, and each one connects in one of the ways below. "
            "Find your tool below to see which one applies to you."
        ),
        "legend_title": "How to connect",
        "legend_head": "| Mode | What you do | Integrations |\n|---|---|---|",
        "find_tip": "Looking for a specific tool? Use your browser's search (Ctrl+F or Cmd+F) on this page.",
        "col_tool": "Integration",
        "col_where": "Where to find the API key",
        "col_fields": "Fields to fill in",
        "modes": {
            "oauth": {
                "name": "One-click sign-in",
                "short": "Sign in to your tool, nothing to copy",
                "icon": "right-to-bracket",
                "body": (
                    "The simplest mode. WonkaChat sends you to the official sign-in page of the tool, "
                    "you sign in with your usual account and accept the access. WonkaChat never sees your password."
                ),
                "steps": [
                    "Go to **Customize → Connectors** and open the integration.",
                    "Click **Connect**. A sign-in window for the tool opens.",
                    "Sign in with your usual account and accept the requested access.",
                    "You come back to WonkaChat automatically: the integration shows as connected.",
                ],
            },
            "api_key": {
                "name": "API key",
                "short": "Copy a key from your tool and paste it",
                "icon": "key",
                "body": (
                    "Some tools do not offer sign-in for third-party apps. Instead, you create an **API key** "
                    "(a long secret code) in the tool and paste it once in WonkaChat."
                ),
                "steps": [
                    "In the tool, create an API key (see the table below for where to find it).",
                    "In WonkaChat, go to **Customize → Connectors**, open the integration and click **Connect**.",
                    "Paste the key in the secure form that opens, then confirm.",
                ],
                "warning": (
                    "An API key gives access to your account: never share it in a conversation. "
                    "Only paste it in the connection form. If it leaks, delete it in the tool and create a new one."
                ),
            },
            "credentials": {
                "name": "Your tool's details",
                "short": "Fill in the address and access details of your tool",
                "icon": "server",
                "body": (
                    "These integrations are hosted by Wonka AI and connect to **your own instance** of the tool. "
                    "WonkaChat needs to know where your instance is and which account to use."
                ),
                "steps": [
                    "Gather the details listed in the table below for your tool.",
                    "In WonkaChat, go to **Customize → Connectors**, open the integration and click **Connect**.",
                    "Fill in each field and save. WonkaChat checks the connection right away.",
                ],
                "tip": "Your details are stored encrypted and only used for your own requests.",
            },
            "assisted": {
                "name": "Set up with Wonka",
                "short": "We activate it for your organization",
                "icon": "handshake",
                "body": (
                    "These integrations need a setup on Wonka AI's side for your organization "
                    "(for example an agreement with the software vendor). Once it is done, they appear in your connectors."
                ),
                "steps": [
                    "Contact us from the [Getting help](/en/support-resources/getting-help) page and name the tool.",
                    "We activate the integration for your organization and tell you when it is ready.",
                    "Open it in **Customize → Connectors** and click **Connect**.",
                ],
            },
        },
        "missing_title": "Your tool is not in the list?",
        "missing_custom": (
            "If your tool exposes an MCP server, an administrator can add it as a "
            "[custom connector](/en/tools-connection/custom-connectors) in a few minutes."
        ),
        "missing_request": (
            "Otherwise, ask us for it from the [Getting help](/en/support-resources/getting-help) page: "
            "new integrations are added every week."
        ),
        "trouble": (
            "Connection fails or the integration stops working? See "
            "[Troubleshooting connections](/en/tools-connection/troubleshooting-connections)."
        ),
    },
    "fr": {
        "title": "Toutes les intégrations",
        "description": "Tous les connecteurs disponibles dans WonkaChat et comment les connecter, sur une seule page.",
        "intro": (
            "WonkaChat propose plus de {count} intégrations prêtes à l'emploi. Elles se trouvent toutes dans "
            "**Personnaliser → Connecteurs**, et chacune se connecte d'une des façons ci-dessous. "
            "Cherchez votre outil pour savoir laquelle vous concerne."
        ),
        "legend_title": "Comment se connecter",
        "legend_head": "| Mode | Ce que vous faites | Intégrations |\n|---|---|---|",
        "find_tip": "Vous cherchez un outil précis ? Utilisez la recherche de votre navigateur (Ctrl+F ou Cmd+F) sur cette page.",
        "col_tool": "Intégration",
        "col_where": "Où trouver la clé API",
        "col_fields": "Champs à remplir",
        "modes": {
            "oauth": {
                "name": "Connexion en un clic",
                "short": "Connectez-vous à votre outil, rien à copier",
                "icon": "right-to-bracket",
                "body": (
                    "Le mode le plus simple. WonkaChat vous envoie vers la page de connexion officielle de l'outil, "
                    "vous vous connectez avec votre compte habituel et vous acceptez l'accès. "
                    "WonkaChat ne voit jamais votre mot de passe."
                ),
                "steps": [
                    "Allez dans **Personnaliser → Connecteurs** et ouvrez l'intégration.",
                    "Cliquez sur **Se connecter**. Une fenêtre de connexion de l'outil s'ouvre.",
                    "Connectez-vous avec votre compte habituel et acceptez les accès demandés.",
                    "Vous revenez automatiquement dans WonkaChat : l'intégration apparaît comme connectée.",
                ],
            },
            "api_key": {
                "name": "Clé API",
                "short": "Copiez une clé depuis votre outil et collez-la",
                "icon": "key",
                "body": (
                    "Certains outils ne proposent pas de connexion pour les applications tierces. À la place, "
                    "vous créez une **clé API** (un long code secret) dans l'outil et vous la collez une fois dans WonkaChat."
                ),
                "steps": [
                    "Dans l'outil, créez une clé API (voir le tableau ci-dessous pour savoir où la trouver).",
                    "Dans WonkaChat, allez dans **Personnaliser → Connecteurs**, ouvrez l'intégration et cliquez sur **Se connecter**.",
                    "Collez la clé dans le formulaire sécurisé qui s'ouvre, puis validez.",
                ],
                "warning": (
                    "Une clé API donne accès à votre compte : ne la partagez jamais dans une conversation. "
                    "Collez-la uniquement dans le formulaire de connexion. En cas de fuite, supprimez-la dans l'outil et créez-en une nouvelle."
                ),
            },
            "credentials": {
                "name": "Informations de votre outil",
                "short": "Renseignez l'adresse et les accès de votre outil",
                "icon": "server",
                "body": (
                    "Ces intégrations sont hébergées par Wonka AI et se connectent à **votre propre instance** de l'outil. "
                    "WonkaChat a besoin de savoir où se trouve votre instance et quel compte utiliser."
                ),
                "steps": [
                    "Rassemblez les informations listées dans le tableau ci-dessous pour votre outil.",
                    "Dans WonkaChat, allez dans **Personnaliser → Connecteurs**, ouvrez l'intégration et cliquez sur **Se connecter**.",
                    "Remplissez chaque champ et enregistrez. WonkaChat vérifie la connexion immédiatement.",
                ],
                "tip": "Vos informations sont stockées chiffrées et utilisées uniquement pour vos propres demandes.",
            },
            "assisted": {
                "name": "Mise en place avec Wonka",
                "short": "Nous l'activons pour votre organisation",
                "icon": "handshake",
                "body": (
                    "Ces intégrations demandent une mise en place côté Wonka AI pour votre organisation "
                    "(par exemple un accord avec l'éditeur du logiciel). Une fois faite, elles apparaissent dans vos connecteurs."
                ),
                "steps": [
                    "Contactez-nous depuis la page [Obtenir de l'aide](/fr/support-resources/getting-help) en précisant l'outil.",
                    "Nous activons l'intégration pour votre organisation et vous prévenons quand elle est prête.",
                    "Ouvrez-la dans **Personnaliser → Connecteurs** et cliquez sur **Se connecter**.",
                ],
            },
        },
        "missing_title": "Votre outil n'est pas dans la liste ?",
        "missing_custom": (
            "Si votre outil propose un serveur MCP, un administrateur peut l'ajouter comme "
            "[connecteur personnalisé](/fr/tools-connection/custom-connectors) en quelques minutes."
        ),
        "missing_request": (
            "Sinon, demandez-le-nous depuis la page [Obtenir de l'aide](/fr/support-resources/getting-help) : "
            "de nouvelles intégrations sont ajoutées chaque semaine."
        ),
        "trouble": (
            "La connexion échoue ou l'intégration ne répond plus ? Consultez "
            "[Dépannage des connexions](/fr/tools-connection/troubleshooting-connections)."
        ),
    },
    "nl": {
        "title": "Alle integraties",
        "description": "Alle connectoren in WonkaChat en hoe u ze koppelt, op één pagina.",
        "intro": (
            "WonkaChat biedt meer dan {count} kant-en-klare integraties. U vindt ze allemaal in "
            "**Aanpassen → Connectoren**, en elke integratie wordt op een van de onderstaande manieren gekoppeld. "
            "Zoek uw tool op om te zien welke manier voor u geldt."
        ),
        "legend_title": "Hoe koppelen",
        "legend_head": "| Modus | Wat u doet | Integraties |\n|---|---|---|",
        "find_tip": "Zoekt u een specifieke tool? Gebruik de zoekfunctie van uw browser (Ctrl+F of Cmd+F) op deze pagina.",
        "col_tool": "Integratie",
        "col_where": "Waar vindt u de API-sleutel",
        "col_fields": "In te vullen velden",
        "modes": {
            "oauth": {
                "name": "Aanmelden in één klik",
                "short": "Meld u aan bij uw tool, niets te kopiëren",
                "icon": "right-to-bracket",
                "body": (
                    "De eenvoudigste manier. WonkaChat stuurt u naar de officiële aanmeldpagina van de tool, "
                    "u meldt zich aan met uw gewone account en geeft toegang. WonkaChat ziet uw wachtwoord nooit."
                ),
                "steps": [
                    "Ga naar **Aanpassen → Connectoren** en open de integratie.",
                    "Klik op **Verbinden**. Er opent een aanmeldvenster van de tool.",
                    "Meld u aan met uw gewone account en accepteer de gevraagde toegang.",
                    "U keert automatisch terug naar WonkaChat: de integratie staat als verbonden.",
                ],
            },
            "api_key": {
                "name": "API-sleutel",
                "short": "Kopieer een sleutel uit uw tool en plak hem",
                "icon": "key",
                "body": (
                    "Sommige tools bieden geen aanmelding voor externe apps. In plaats daarvan maakt u in de tool een "
                    "**API-sleutel** aan (een lange geheime code) en plakt u die één keer in WonkaChat."
                ),
                "steps": [
                    "Maak in de tool een API-sleutel aan (zie de tabel hieronder voor waar u die vindt).",
                    "Ga in WonkaChat naar **Aanpassen → Connectoren**, open de integratie en klik op **Verbinden**.",
                    "Plak de sleutel in het beveiligde formulier dat opent en bevestig.",
                ],
                "warning": (
                    "Een API-sleutel geeft toegang tot uw account: deel hem nooit in een gesprek. "
                    "Plak hem alleen in het verbindingsformulier. Is hij uitgelekt, verwijder hem dan in de tool en maak een nieuwe aan."
                ),
            },
            "credentials": {
                "name": "Gegevens van uw tool",
                "short": "Vul het adres en de toegangsgegevens van uw tool in",
                "icon": "server",
                "body": (
                    "Deze integraties worden gehost door Wonka AI en verbinden met **uw eigen omgeving** van de tool. "
                    "WonkaChat moet weten waar uw omgeving staat en welk account het moet gebruiken."
                ),
                "steps": [
                    "Verzamel de gegevens uit de tabel hieronder voor uw tool.",
                    "Ga in WonkaChat naar **Aanpassen → Connectoren**, open de integratie en klik op **Verbinden**.",
                    "Vul elk veld in en sla op. WonkaChat controleert de verbinding meteen.",
                ],
                "tip": "Uw gegevens worden versleuteld opgeslagen en alleen gebruikt voor uw eigen verzoeken.",
            },
            "assisted": {
                "name": "Instellen met Wonka",
                "short": "Wij activeren het voor uw organisatie",
                "icon": "handshake",
                "body": (
                    "Deze integraties vereisen een configuratie aan de kant van Wonka AI voor uw organisatie "
                    "(bijvoorbeeld een akkoord met de softwareleverancier). Daarna verschijnen ze bij uw connectoren."
                ),
                "steps": [
                    "Neem contact met ons op via de pagina [Hulp krijgen](/nl/support-resources/getting-help) en noem de tool.",
                    "Wij activeren de integratie voor uw organisatie en laten u weten wanneer ze klaar is.",
                    "Open ze in **Aanpassen → Connectoren** en klik op **Verbinden**.",
                ],
            },
        },
        "missing_title": "Staat uw tool er niet tussen?",
        "missing_custom": (
            "Als uw tool een MCP-server aanbiedt, kan een beheerder die in enkele minuten toevoegen als "
            "[aangepaste connector](/nl/tools-connection/custom-connectors)."
        ),
        "missing_request": (
            "Vraag het ons anders via de pagina [Hulp krijgen](/nl/support-resources/getting-help): "
            "er komen elke week nieuwe integraties bij."
        ),
        "trouble": (
            "Mislukt de verbinding of werkt de integratie niet meer? Zie "
            "[Problemen met verbindingen oplossen](/nl/tools-connection/troubleshooting-connections)."
        ),
    },
}

ANCHORS = {"oauth": "oauth", "api_key": "api-key", "credentials": "credentials", "assisted": "assisted"}


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def attr(text: str) -> str:
    return text.replace('"', "&quot;")


def logo(url: str) -> str:
    if not url:
        return ""
    return f'<img src="{url}" alt="" width="20" height="20" noZoom className="inline m-0" /> '


def render(lang: str, rows: list) -> str:
    t = T[lang]
    by_mode = {m: [r for r in rows if r["mode"] == m] for m in MODES}
    out = [
        "---",
        f'title: "{t["title"]}"',
        f'description: "{t["description"]}"',
        "---",
        "",
        "{/* Generated by scripts/integrations/build.py. Do not edit by hand: edit catalog.yaml or the script, then run `build.py generate`. */}",
        "",
        t["intro"].format(count=(len(rows) // 10) * 10),
        "",
        f"## {t['legend_title']}",
        "",
        t["legend_head"],
    ]
    for m in (m for m in MODES if by_mode[m]):
        mt = t["modes"][m]
        out.append(f"| [{mt['name']}](#{ANCHORS[m]}) | {mt['short']} | {len(by_mode[m])} |")
    out += ["", f"<Tip>{t['find_tip']}</Tip>", ""]

    for m in MODES:
        mt = t["modes"][m]
        items = by_mode[m]
        if not items:
            continue
        out += [f'<a id="{ANCHORS[m]}"></a>', "", f"## {mt['name']}", "", mt["body"], ""]
        out += [f"{i}. {step}" for i, step in enumerate(mt["steps"], 1)]
        out.append("")
        if "warning" in mt:
            out += [f"<Warning>{mt['warning']}</Warning>", ""]
        if "tip" in mt:
            out += [f"<Tip>{mt['tip']}</Tip>", ""]

        if m == "api_key":
            out += [f"| {t['col_tool']} | {t['col_where']} |", "|---|---|"]
            for r in items:
                out.append(f"| {logo(r['icon'])}**{cell(r['name'])}** | {cell(r['hint'])} |")
        elif m == "credentials":
            out += [f"| {t['col_tool']} | {t['col_fields']} |", "|---|---|"]
            for r in items:
                out.append(f"| {logo(r['icon'])}**{cell(r['name'])}** | {cell(', '.join(r['fields']))} |")
        else:
            # Nothing tool-specific to say: a grid of logos is easier to scan than a table.
            out.append("<CardGroup cols={3}>")
            for r in items:
                icon = f' icon="{r["icon"]}"' if r["icon"] else ""
                if r["note"]:
                    out += [f'<Card title="{attr(r["name"])}"{icon}>', r["note"], "</Card>"]
                else:
                    out.append(f'<Card title="{attr(r["name"])}"{icon} />')
            out.append("</CardGroup>")
        out.append("")

    out += [
        f"## {t['missing_title']}",
        "",
        t["missing_custom"],
        "",
        t["missing_request"],
        "",
        f"<Info>{t['trouble']}</Info>",
        "",
    ]
    return "\n".join(out)


def generate(_args) -> None:
    servers = json.loads(SERVERS_JSON.read_text())
    catalog = yaml.safe_load(CATALOG_YAML.read_text())
    hidden = set(catalog.get("hidden") or [])
    overrides = catalog.get("modes") or {}
    names = catalog.get("names") or {}
    hints = catalog.get("api_key_hints") or {}
    notes = catalog.get("notes") or {}

    # A legacy connector is hidden when a newer generation of it exists (slack -> slack_v2).
    current_families = {family(k) for k, e in servers.items() if not e["legacy"]}

    base_rows = []
    for key, entry in servers.items():
        if key in hidden or (entry["legacy"] and family(key) in current_families):
            continue
        mode = connection_mode(key, entry, overrides)
        if mode not in MODES:
            sys.exit(f"Unknown mode '{mode}' for '{key}'")
        base_rows.append(
            {
                "key": key,
                "mode": mode,
                "name": display_name(key, names),
                "icon": entry["iconURL"],
                "fields": [f["title"] for f in entry["userFields"]],
            }
        )
    base_rows.sort(key=lambda r: r["name"].lower())

    for lang in LANGS:
        rows = []
        for r in base_rows:
            row = dict(r)
            if r["mode"] == "api_key":
                hint = (hints.get(r["key"]) or {}).get(lang)
                if not hint:
                    print(f"WARNING: no API key hint for '{r['key']}' ({lang})", file=sys.stderr)
                row["hint"] = hint or "—"
            row["note"] = (notes.get(r["key"]) or {}).get(lang, "")
            labels = FIELD_LABELS.get(lang, {})
            row["fields"] = [labels.get(f, f) for f in r["fields"]]
            rows.append(row)
        path = ROOT / lang / f"{PAGE_SLUG}.mdx"
        path.write_text(render(lang, rows))
        print(f"Wrote {path.relative_to(ROOT)} ({len(rows)} integrations)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_sync = sub.add_parser("sync", help="refresh servers.json from the Config repo and Composio")
    p_sync.add_argument("--config", required=True, help="path to a local clone of the Config repo")
    p_sync.add_argument("--ref", default="origin/main", help="git ref of the Config repo to read")
    p_sync.add_argument("--no-fetch", dest="fetch", action="store_false", help="skip git fetch")
    p_sync.set_defaults(func=sync)
    p_gen = sub.add_parser("generate", help="write the MDX pages from servers.json")
    p_gen.set_defaults(func=generate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
