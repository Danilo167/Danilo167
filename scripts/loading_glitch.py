from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import html
import random

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"

entrada = PASTA_ASSETS / "foto_ascii.svg"
saida = PASTA_ASSETS / "foto_loading_glitch.gif"

largura = 800
altura = 450
frames_total = 50

cor = (142, 110, 193)
cor_falha = (190, 150, 255)
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

inicio_x = int(
    (largura - largura_arte) / 2
)

inicio_y = int(
    (altura - altura_arte) / 2 - 25
)

frames = []

random.seed()

for frame in range(frames_total):

    imagem = Image.new(
        "RGBA",
        (largura, altura),
        (*fundo, 255)
    )

    progresso = min(
        1,
        frame / (frames_total - 1)
    )

    caracteres_visiveis = int(
        len(linhas) * progresso
    )

    camada = Image.new(
        "RGBA",
        (largura, altura),
        (0, 0, 0, 0)
    )

    desenho_ascii = ImageDraw.Draw(camada)

    for indice in range(caracteres_visiveis):

        linha = linhas[indice]

        if indice == caracteres_visiveis - 1:

            quantidade = int(
                len(linha) * progresso
            )

            linha = linha[:quantidade]

        desenho_ascii.text(
            (
                inicio_x,
                inicio_y + indice * altura_linha
            ),
            linha,
            font=fonte,
            fill=(*cor, 255)
        )

    if random.random() < 0.35 and caracteres_visiveis > 3:

        quantidade_falhas = random.randint(1, 3)

        for _ in range(quantidade_falhas):

            linha_falha = random.randint(
                0,
                caracteres_visiveis - 1
            )

            y = int(
                inicio_y
                + linha_falha * altura_linha
            )

            if y < 0 or y >= altura:
                continue

            altura_falha = random.randint(2, 4)

            y_final = min(
                altura,
                y + altura_falha
            )

            if y_final <= y:
                continue

            x1 = max(
                0,
                inicio_x - 20
            )

            x2 = min(
                largura,
                inicio_x + int(largura_arte) + 20
            )

            if x2 <= x1:
                continue

            deslocamento = random.randint(
                -20,
                20
            )

            recorte = camada.crop(
                (
                    x1,
                    y,
                    x2,
                    y_final
                )
            )

            novo_x = x1 + deslocamento

            novo_x = max(
                0,
                min(
                    largura - recorte.width,
                    novo_x
                )
            )

            camada.paste(
                recorte,
                (
                    novo_x,
                    y
                )
            )

            desenho_falha = ImageDraw.Draw(
                camada
            )

            faixa_largura = random.randint(
                10,
                60
            )

            faixa_x = random.randint(
                x1,
                max(
                    x1,
                    x2 - faixa_largura
                )
            )

            faixa_x2 = min(
                x2,
                faixa_x + faixa_largura
            )

            if faixa_x2 > faixa_x:

                desenho_falha.rectangle(
                    (
                        faixa_x,
                        y,
                        faixa_x2,
                        y_final
                    ),
                    fill=(*cor_falha, 180)
                )

    imagem = Image.alpha_composite(
        imagem,
        camada
    )

    desenho = ImageDraw.Draw(imagem)

    barra_largura = 360
    barra_altura = 8

    barra_x = int(
        (largura - barra_largura) / 2
    )

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

    texto_largura = (
        caixa[2] - caixa[0]
    )

    desenho.text(
        (
            int((largura - texto_largura) / 2),
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

    frames.append(
        frame_final.copy()
    )

if saida.exists():

    saida.unlink()

frames[0].save(
    saida,
    save_all=True,
    append_images=frames[1:],
    duration=87,
    loop=0,
    optimize=False
)

print("Efeito Loading + Glitch criado com sucesso!")
print("Tempo em 100%: aproximadamente 15 segundos.")
print(f"Arquivo: {saida}")
print(f"Tamanho: {saida.stat().st_size} bytes")