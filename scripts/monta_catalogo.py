"""Monta o catálogo: metadados do OpenAlex, tentativa de download dos PDFs de acesso aberto e geração de
catalogo.json / catalogo.csv / CATALOGO.md. Uso: python3 scripts/monta_catalogo.py [--sem-download]"""
import csv, json, re, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lista import LISTA, MANUAIS, IGNORAR_PDF

RAIZ = Path(__file__).resolve().parents[1]
PDFS = RAIZ / "pdfs"
CACHE = RAIZ / "scripts" / ".cache_openalex"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SECOES = {"A": "Fuzzy aplicado ao transplante renal (e de órgãos)", "B": "Estado da arte do fuzzy (geral)",
          "C": "Contexto: extração de regras e predição em transplante renal (não fuzzy)"}


def api(ident):
    chave = ident if ident.startswith("W") else "https://doi.org/" + ident[4:]
    url = "https://api.openalex.org/works/" + urllib.parse.quote(chave, safe=":/")
    cache = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", ident) + ".json")
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
    for tentativa in range(6):
        try:
            w = json.load(urllib.request.urlopen(req, timeout=60))
            break
        except Exception as e:
            erro = e
            time.sleep(3 * (tentativa + 1))
    else:
        raise erro
    CACHE.mkdir(exist_ok=True)
    cache.write_text(json.dumps(w, ensure_ascii=False), encoding="utf-8")
    return w


def resumo(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = sorted((i, p) for p, ii in inv.items() for i in ii)
    return " ".join(p for _, p in pos)


def slug(s, n=50):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:n]


def candidatos(w):
    urls = []
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    locs = [w.get("best_oa_location") or {}] + (w.get("locations") or [])
    for l in locs:
        for k in ("pdf_url", "landing_page_url"):
            u = l.get(k)
            if not u:
                continue
            m = re.search(r"arxiv\.org/(?:abs|pdf)/([\w.\-/]+?)(?:v\d+)?(?:\.pdf)?$", u)
            if m:
                urls.append(f"https://arxiv.org/pdf/{m.group(1)}")
            m = re.search(r"(PMC\d+)", u)
            if m:
                urls.append(f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={m.group(1)}&blobtype=pdf")
                urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{m.group(1)}/pdf/")
            if k == "pdf_url":
                urls.append(u)
            elif "mdpi.com" in u:
                urls.append(u.rstrip("/") + "/pdf")
            elif "hal.science" in u or "hal.archives" in u:
                urls.append(u.rstrip("/") + "/document")
            elif "zenodo.org" in u or "preprints.org" in u or "researchsquare" in u:
                urls.append(u)
    pmcid = ((w.get("ids") or {}).get("pmcid") or "")
    m = re.search(r"(\d{5,})", pmcid)
    if m:
        urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{m.group(1)}/pdf/")
        urls.append(f"https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC{m.group(1)}&blobtype=pdf")
    oa = (w.get("open_access") or {}).get("oa_url")
    if oa:
        urls.append(oa)
    if doi and (w.get("open_access") or {}).get("is_oa"):
        if doi.startswith(("10.1186/", "10.1007/", "10.1038/")):
            urls.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
        if doi.startswith("10.1371/"):
            j = {"pone": "plosone", "pcbi": "ploscompbiol"}.get(doi.split(".")[2], "plosone")
            urls.append(f"https://journals.plos.org/{j}/article/file?id={doi}&type=printable")
        if doi.startswith("10.1155/"):
            urls.append(f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}")
        if doi.startswith("10.3389/"):
            urls.append(f"https://www.frontiersin.org/articles/{doi}/pdf")
        urls.append("https://doi.org/" + doi)
    vistos, out = set(), []
    for u in urls:
        if u not in vistos:
            vistos.add(u)
            out.append(u)
    return out


def baixa(urls, destino):
    if destino.exists() and destino.stat().st_size > 20000:
        return "ja_baixado"
    tmp = destino.with_suffix(".tmp")
    for u, ua in [(u, ua) for u in urls for ua in (None, UA)]:
        try:
            subprocess.run(["curl", "-sL", "--max-time", "60"] + (["-A", ua] if ua else []) + ["-H", "Accept: application/pdf,*/*", "-o", str(tmp), u],
                           check=False, timeout=90)
            if tmp.exists() and tmp.stat().st_size > 20000 and tmp.read_bytes()[:5] == b"%PDF-":
                tmp.rename(destino)
                return u
        except Exception:
            pass
    tmp.unlink(missing_ok=True)
    return None


def processa(item):
    secao, ident, rel, nota = item
    try:
        w = api(ident)
    except Exception as e:
        return dict(secao=secao, relevancia=rel, nota=nota, id=ident, titulo=f"(falha ao consultar {ident}: {e})", autores=[], ano=None,
                    venue="", doi="", url="", citacoes=None, acesso_aberto=False, pdf=None, pdf_origem=None, urls=[], resumo="", menciona_fuzzy=None)
    autores = [a["author"]["display_name"] for a in w.get("authorships", [])]
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    ab = resumo(w)
    texto = (w.get("title") or "") + " " + ab
    return dict(secao=secao, relevancia=rel, nota=nota, id=w["id"].rsplit("/", 1)[-1], titulo=w.get("title") or "", autores=autores,
                ano=w.get("publication_year"), venue=venue, doi=doi, tipo=w.get("type"),
                url=("https://doi.org/" + doi) if doi else ((w.get("primary_location") or {}).get("landing_page_url") or w["id"]),
                licenca=(w.get("best_oa_location") or {}).get("license") or "", status_oa=(w.get("open_access") or {}).get("oa_status") or "",
                citacoes=w.get("cited_by_count"), acesso_aberto=bool((w.get("open_access") or {}).get("is_oa")),
                urls=candidatos(w), resumo=ab, menciona_fuzzy=(bool(re.search(r"fuzz|neuro-fuzzy|anfis|graded logic|LSP", texto, re.I)) if ab else None))


def ref(it):
    au = it["autores"]
    nomes = ", ".join(au[:3]) + (" et al." if len(au) > 3 else "")
    return f"{nomes} ({it['ano'] or 's.d.'}). [{it['titulo']}]({it['url']}). *{it['venue'] or it.get('tipo') or ''}*."


def escreve_md(itens):
    L = ["# Catálogo — estado da arte do fuzzy e do fuzzy aplicado ao transplante renal", "",
         "Gerado por `scripts/monta_catalogo.py` a partir da lista curada em `scripts/lista.py` (metadados do OpenAlex). "
         "Os mesmos dados estão em `catalogo.csv` e `catalogo.json` (este com o resumo de cada artigo).", "",
         f"**{len(itens)} trabalhos** · **{sum(1 for i in itens if i['pdf'])} com PDF em `pdfs/`** · "
         f"**{sum(1 for i in itens if not i['pdf'])} sem PDF** (situação indicada em cada linha).", "",
         "Dentro de cada seção os trabalhos estão em **ordem decrescente de relevância** (coluna #). A relevância (alta, média, baixa) "
         "foi julgada pelo título e pelo resumo, em relação ao tema da seção e ao uso no projeto HLAGyn (regras fuzzy interpretáveis "
         "para risco de perda do enxerto renal); não é uma medida de qualidade do artigo.", "",
         "Coluna PDF: link = arquivo baixado; **não baixado (aberto)** = o artigo é de acesso aberto, mas o site recusou o download "
         "automático (baixar pelo link do título); **não baixado (pago)** = sem cópia aberta localizada.", ""]
    for sec, nome in SECOES.items():
        L += [f"## {sec}. {nome}", "", "| # | Relevância | Referência | Citações | PDF | Nota |", "|---|---|---|---|---|---|"]
        for it in [x for x in itens if x["secao"] == sec]:
            pdf = f"[PDF]({it['pdf']})" if it["pdf"] else ("**não baixado (aberto)**" if it["acesso_aberto"] else "**não baixado (pago)**")
            nota = it["nota"]
            if it["menciona_fuzzy"] is False and sec in "AB":
                nota += " O resumo não menciona fuzzy."
            L.append(f"| {it['codigo']} | {it['relevancia']} | {ref(it)} | {it['citacoes'] if it['citacoes'] is not None else '—'} | {pdf} | {nota} |".replace("\n", " "))
        L.append("")
    (RAIZ / "CATALOGO.md").write_text("\n".join(L), encoding="utf-8")


def main():
    with ThreadPoolExecutor(2) as ex:
        itens = list(ex.map(processa, LISTA))
    for m in MANUAIS:
        it = dict(secao=m["secao"], relevancia=m["relevancia"], nota=m["nota"], id="", titulo=m["titulo"], autores=m["autores"], ano=m["ano"],
                  venue=m["venue"], doi=m["doi"], tipo="article", url=m["url"], citacoes=None, acesso_aberto=True, licenca="", status_oa="", urls=[m["url"]], resumo="", menciona_fuzzy=None)
        pos = next((i for i, x in enumerate(itens) if x["id"] == m.get("posicao_apos")), len(itens) - 1)
        itens.insert(pos + 1, it)
    cont = {}
    for it in itens:
        cont[it["secao"]] = cont.get(it["secao"], 0) + 1
        it["ordem"] = cont[it["secao"]]
        it["codigo"] = f"{it['secao']}{it['ordem']:02d}"
        sobrenome = slug((it["autores"][0].split()[-1] if it["autores"] and not it["autores"][0].startswith("(") else "sn"), 20)
        it["arquivo"] = f"{it['codigo']}_{sobrenome}_{it['ano'] or 'sd'}_{slug(it['titulo'], 45)}.pdf"
    PDFS.mkdir(exist_ok=True)

    def dl(it):
        if "--sem-download" in sys.argv:
            ok = "ja_baixado" if (PDFS / it["arquivo"]).exists() else None
        elif it["id"] in IGNORAR_PDF:
            ok = None
        else:
            ok = baixa(it["urls"], PDFS / it["arquivo"])
        it["pdf"] = f"pdfs/{it['arquivo']}" if ok else None
        it["pdf_origem"] = ok if ok and ok != "ja_baixado" else it.get("pdf_origem")
        return it
    with ThreadPoolExecutor(8) as ex:
        itens = list(ex.map(dl, itens))
    antigo = {}
    if (RAIZ / "catalogo.json").exists():
        antigo = {x["codigo"]: x for x in json.loads((RAIZ / "catalogo.json").read_text(encoding="utf-8"))}
    for it in itens:
        if it["pdf"] and not it.get("pdf_origem"):
            it["pdf_origem"] = (antigo.get(it["codigo"]) or {}).get("pdf_origem")
        it["situacao_pdf"] = "baixado" if it["pdf"] else ("não foi possível baixar (acesso aberto, download automático bloqueado)" if it["acesso_aberto"]
                                                          else "não foi possível baixar (acesso pago ou sem cópia aberta)")
    (RAIZ / "catalogo.json").write_text(json.dumps([{k: v for k, v in it.items() if k != "urls"} for it in itens], ensure_ascii=False, indent=1), encoding="utf-8")
    with open(RAIZ / "catalogo.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["codigo", "secao", "ordem_relevancia", "relevancia", "titulo", "autores", "ano", "veiculo", "doi", "url", "citacoes", "acesso_aberto", "licenca", "situacao_pdf", "arquivo_pdf", "nota"])
        for it in itens:
            wr.writerow([it["codigo"], SECOES[it["secao"]], it["ordem"], it["relevancia"], it["titulo"], "; ".join(it["autores"][:6]) + (" et al." if len(it["autores"]) > 6 else ""),
                         it["ano"], it["venue"], it["doi"], it["url"], it["citacoes"], "sim" if it["acesso_aberto"] else "não", it.get("licenca", ""), it["situacao_pdf"], it["pdf"] or "", it["nota"]])
    escreve_md(itens)
    n_ok = sum(1 for it in itens if it["pdf"])
    print(f"{len(itens)} itens | {n_ok} PDFs baixados | {len(itens) - n_ok} sem PDF")
    for it in itens:
        print(f"{it['codigo']} {'PDF' if it['pdf'] else '---'} fz={it['menciona_fuzzy']} {it['ano']} {it['titulo'][:80]}")


if __name__ == "__main__":
    main()
