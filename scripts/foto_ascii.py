import html
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"

imagens = (
    list(PASTA_ASSETS.glob("*.jpg"))
    + list(PASTA_ASSETS.glob("*.png"))
    + list(PASTA_ASSETS.glob("*.jpeg"))
)

if not imagens:
    raise FileNotFoundError(f"Nenhuma imagem encontrada em: {PASTA_ASSETS}")

entrada = PASTA_ASSETS / "foto.png"

if not entrada.exists():
    entrada = imagens[0]

saida = PASTA_ASSETS / "foto_ascii.svg"

caracteres = " .·:;+=*#%@"

cor = "#8E6EC1"

imagem = Image.open(entrada)

imagem = ImageOps.exif_transpose(imagem)

imagem = imagem.convert("L")

imagem = imagem.filter(ImageFilter.MedianFilter(size=3))

imagem = imagem.filter(
    ImageFilter.UnsharpMask(
        radius=1.2,
        percent=180,
        threshold=3
    )
)

imagem = ImageEnhance.Contrast(imagem).enhance(1.5)

imagem = ImageOps.autocontrast(imagem, cutoff=1)

imagem = ImageEnhance.Brightness(imagem).enhance(1.05)

gamma = 0.9

tabela_gamma = [
    int(((i / 255) ** gamma) * 255)
    for i in range(256)
]

imagem = imagem.point(tabela_gamma)

largura = 240

proporcao = imagem.height / imagem.width

fator_aspecto = 0.52

altura = int(
    largura
    * proporcao
    * fator_aspecto
)

imagem = imagem.resize(
    (largura, altura),
    Image.Resampling.LANCZOS
)

linhas_ascii = []

num_chars = len(caracteres) - 1

for y in range(imagem.height):

    linha = ""

    for x in range(imagem.width):

        pixel = imagem.getpixel((x, y))

        indice = pixel * num_chars // 255

        linha += caracteres[indice]

    linhas_ascii.append(
        html.escape(linha)
    )

tamanho_fonte = 8

largura_caractere = tamanho_fonte * 0.60
altura_linha = tamanho_fonte * 1.0

largura_svg = int(
    largura * largura_caractere
)

altura_svg = int(
    altura * altura_linha
)

svg_linhas = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{largura_svg}" '
    f'height="{altura_svg}" '
    f'viewBox="0 0 {largura_svg} {altura_svg}">',

    '<rect '
    'width="100%" '
    'height="100%" '
    'fill="#000000"/>',

    f'<text '
    f'font-family="Courier New, monospace" '
    f'font-size="{tamanho_fonte}px" '
    f'fill="{cor}" '
    f'xml:space="preserve">'
]

for i, linha in enumerate(linhas_ascii):

    y = (i + 1) * altura_linha

    svg_linhas.append(
        f'  <tspan '
        f'x="0" '
        f'y="{y:.1f}">'
        f'{linha}'
        f'</tspan>'
    )

svg_linhas.append("</text>")
svg_linhas.append("</svg>")

with open(
    saida,
    "w",
    encoding="utf-8"
) as arquivo:

    arquivo.write(
        "\n".join(svg_linhas)
    )

print("Arte ASCII melhorada com sucesso!")
print(f"Imagem lida: {entrada.name}")
print(f"Resolução ASCII: {largura} x {altura}")
print(f"Ficheiro guardado em: {saida}")
