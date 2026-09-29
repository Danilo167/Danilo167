import html
from pathlib import Path
from PIL import Image, ImageOps

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"

imagens = list(PASTA_ASSETS.glob("*.jpg")) + list(PASTA_ASSETS.glob("*.png")) + list(PASTA_ASSETS.glob("*.jpeg"))

if not imagens:
    raise FileNotFoundError(f"Nenhuma imagem encontrada em: {PASTA_ASSETS}")

entrada = imagens[0]
saida = PASTA_ASSETS / "foto_ascii.svg"

caracteres = ".:."
cor = "#8E6EC1"

imagem = Image.open(entrada)

imagem = ImageOps.exif_transpose(imagem)

imagem = imagem.convert("L")
imagem = ImageOps.autocontrast(imagem)

largura = 120
proporcao = imagem.height / imagem.width
altura = int(largura * proporcao * 0.5)

imagem = imagem.resize((largura, altura))

linhas_ascii = []

for y in range(imagem.height):
    linha = ""
    for x in range(imagem.width):
        pixel = imagem.getpixel((x, y))
        indice = pixel * (len(caracteres) - 1) // 255
        linha += caracteres[indice]
    
    linhas_ascii.append(html.escape(linha))

svg_linhas = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura * 10}" height="{altura * 18}" viewBox="0 0 {largura * 10} {altura * 18}">',
    '<rect width="100%" height="100%" fill="#000000"/>',
    f'<text x="0" y="15" font-family="monospace" font-size="16" fill="{cor}" xml:space="preserve">'
]

for linha in linhas_ascii:
    svg_linhas.append(f'  <tspan x="0" dy="16">{linha}</tspan>')

svg_linhas.append("</text>\n</svg>")

with open(saida, "w", encoding="utf-8") as arquivo:
    arquivo.write("\n".join(svg_linhas))

print("Arte ASCII gerada com sucesso!")
print(f"Imagem lida: {entrada.name}")
print(f"Ficheiro guardado em: {saida}")