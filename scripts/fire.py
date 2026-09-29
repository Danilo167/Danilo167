from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import html
import random
import math

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"

entrada = PASTA_ASSETS / "foto_ascii.svg"
saida = PASTA_ASSETS / "foto_fire.gif"

largura = 800
altura = 450
frames_total = 80

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
    (altura - altura_arte) / 2 - 20
)

random.seed()

particulas = []

for _ in range(180):

    particulas.append(
        {
            "x": random.uniform(
                inicio_x - 40,
                inicio_x + largura_arte + 40
            ),
            "y": random.uniform(
                inicio_y + altura_arte - 10,
                altura
            ),
            "velocidade": random.uniform(
                1.0,
                3.5
            ),
            "tamanho": random.randint(
                1,
                3
            ),
            "fase": random.uniform(
                0,
                math.pi * 2
            )
        }
    )

frames = []

for frame in range(frames_total):

    imagem = Image.new(
        "RGBA",
        (largura, altura),
        (*fundo, 255)
    )

    desenho = ImageDraw.Draw(imagem)

    for particula in particulas:

        particula["y"] -= particula["velocidade"]

        if particula["y"] < inicio_y + altura_arte - 40:

            particula["y"] = altura + random.randint(
                0,
                30
            )

            particula["x"] = random.uniform(
                inicio_x - 40,
                inicio_x + largura_arte + 40
            )

        deslocamento = math.sin(
            frame * 0.15 + particula["fase"]
        ) * 5

        x = int(
            particula["x"] + deslocamento
        )

        y = int(
            particula["y"]
        )

        distancia = (
            altura - y
        ) / max(
            1,
            altura - inicio_y
        )

        tamanho = max(
            1,
            int(
                particula["tamanho"]
                * distancia
                + 1
            )
        )

        intensidade = random.random()

        if intensidade < 0.55:

            cor_fogo = (
                120,
                60,
                170
            )

        elif intensidade < 0.85:

            cor_fogo = (
                180,
                100,
                220
            )

        else:

            cor_fogo = (
                230,
                170,
                255
            )

        desenho.ellipse(
            (
                x,
                y,
                x + tamanho,
                y + tamanho
            ),
            fill=(*cor_fogo, 190)
        )

    for indice, linha in enumerate(linhas):

        desenho.text(
            (
                inicio_x,
                inicio_y + indice * altura_linha
            ),
            linha,
            font=fonte,
            fill=(*cor, 255)
        )

    frames.append(
        imagem.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )
    )

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

print("Efeito Fire criado com sucesso!")
print(f"Arquivo: {saida}")
print(f"Tamanho: {saida.stat().st_size} bytes")