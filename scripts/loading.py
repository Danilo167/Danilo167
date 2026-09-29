from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import html

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"

entrada = PASTA_ASSETS / "foto_ascii.svg"
saida = PASTA_ASSETS / "foto_loading.gif"

largura = 800
altura = 450
frames_total = 50

cor = (142, 110, 193)
fundo = (0, 0, 0)

conteudo = entrada.read_text(encoding="utf-8")

linhas = re.findall(
    r"<tspan[^>]*>(.*?)</tspan>",
    conteudo,
    re.DOTALL
)

linhas = [html.unescape(linha) for linha in linhas]

if not linhas:
    raise ValueError("Nenhuma linha ASCII encontrada no SVG.")

try:
    fonte = ImageFont.truetype(
        "C:/Windows/Fonts/consola.ttf",
        7
    )
except:
    fonte = ImageFont.load_default()

try:
    fonte_loading = ImageFont.truetype(
        "C:/Windows/Fonts/consola.ttf",
        13
    )
except:
    fonte_loading = ImageFont.load_default()

altura_linha = 8
largura_char = 4.2

largura_arte = max(
    len(linha) for linha in linhas
) * largura_char

altura_arte = len(linhas) * altura_linha

inicio_x = (largura - largura_arte) / 2
inicio_y = (altura - altura_arte) / 2 - 25

frames = []

for frame in range(frames_total):

    imagem = Image.new(
        "RGBA",
        (largura, altura),
        (*fundo, 255)
    )

    desenho = ImageDraw.Draw(imagem)

    progresso = min(
        1,
        frame / (frames_total - 1)
    )

    caracteres_visiveis = int(
        len(linhas) * progresso
    )

    for indice in range(caracteres_visiveis):

        linha = linhas[indice]

        if indice == caracteres_visiveis - 1:
            quantidade = int(
                len(linha) * progresso
            )
            linha = linha[:quantidade]

        desenho.text(
            (
                inicio_x,
                inicio_y + indice * altura_linha
            ),
            linha,
            font=fonte,
            fill=(*cor, 255)
        )

    barra_largura = 360
    barra_altura = 8
    barra_x = (largura - barra_largura) / 2
    barra_y = altura - 75

    desenho.rectangle(
        (
            barra_x,
            barra_y,
            barra_x + barra_largura,
            barra_y + barra_altura
        ),
        outline=(*cor, 180),
        width=1
    )

    preenchimento = int(
        (barra_largura - 4) * progresso
    )

    if preenchimento > 0:
        desenho.rectangle(
            (
                barra_x + 2,
                barra_y + 2,
                barra_x + 2 + preenchimento,
                barra_y + barra_altura - 2
            ),
            fill=(*cor, 255)
        )

    porcentagem = int(
        progresso * 100
    )

    texto = f"LOADING... {porcentagem:03d}%"

    caixa = desenho.textbbox(
        (0, 0),
        texto,
        font=fonte_loading
    )

    texto_largura = caixa[2] - caixa[0]

    desenho.text(
        (
            (largura - texto_largura) / 2,
            barra_y + 20
        ),
        texto,
        font=fonte_loading,
        fill=(*cor, 255)
    )

    frames.append(
        imagem.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )
    )

frame_final = frames[-1].copy()

for _ in range(200):
    frames.append(frame_final.copy())

if saida.exists():
    saida.unlink()

frames[0].save(
    saida,
    save_all=True,
    append_images=frames[1:],
    duration=75,
    loop=0,
    optimize=False
)

print("Efeito Loading criado com sucesso!")
print("Carregamento concluído.")
print("Tempo em 100%: aproximadamente 15 segundos.")
print(f"Arquivo: {saida}")
print(f"Tamanho: {saida.stat().st_size} bytes")