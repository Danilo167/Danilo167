import math
import os
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

PASTA_SCRIPTS = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_SCRIPTS.parent
PASTA_ASSETS = PASTA_PROJETO / "assets"
PASTA_ASSETS.mkdir(parents=True, exist_ok=True)
ARQUIVO_SAIDA = PASTA_ASSETS / "transicao_si_farmacia.gif"

LARGURA_FINAL = 480
ALTURA_FINAL = 200
SAIDA_LARGURA = 800
SAIDA_ALTURA = 333
ESCALA = 5

W = LARGURA_FINAL * ESCALA
H = ALTURA_FINAL * ESCALA

CX = W // 2
CY = H // 2

BG_COLOR = (13, 17, 23, 255)
CARD_BORDER = (48, 54, 61, 255)
GRID_DOT = (28, 33, 40, 255)
COR_ROXO = (139, 92, 246, 255)
COR_ROXO_CLARO = (196, 181, 253, 255)
COR_ROXO_BRILHO = (167, 139, 250, 255)
COR_ROXO_PROFUNDO = (109, 40, 217, 255)
COR_CYAN = (56, 189, 248, 255)
COR_BRANCO = (240, 246, 252, 255)


def carregar_fonte(tamanho, negrito=False):
    candidatas = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if negrito else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/Library/Fonts/Menlo.ttc",
        "C:/Windows/Fonts/CascadiaCode.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for caminho in candidatas:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            continue
    try:
        return ImageFont.load_default(tamanho)
    except TypeError:
        return ImageFont.load_default()


fonte_code = carregar_fonte(32 * ESCALA, negrito=True)
fonte_bits = carregar_fonte(11 * ESCALA)


def desenhar_card_base(draw):
    raio = 16 * ESCALA
    draw.rounded_rectangle(
        [8 * ESCALA, 8 * ESCALA, W - 8 * ESCALA, H - 8 * ESCALA],
        radius=raio,
        outline=CARD_BORDER,
        width=int(1.5 * ESCALA)
    )
    espaco = 30 * ESCALA
    for x in range(26 * ESCALA, W - 26 * ESCALA, espaco):
        for y in range(24 * ESCALA, H - 24 * ESCALA, espaco):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=GRID_DOT)


def desenhar_taca_higia(draw, cx, cy, alfa_pct=1.0, pulso=0.0):
    if alfa_pct <= 0:
        return

    cor_linha = (
        int(COR_ROXO_CLARO[0] * alfa_pct),
        int(COR_ROXO_CLARO[1] * alfa_pct),
        int(COR_ROXO_CLARO[2] * alfa_pct),
        int(255 * alfa_pct)
    )
    cor_glow = (
        int(COR_ROXO_BRILHO[0] * alfa_pct),
        int(COR_ROXO_BRILHO[1] * alfa_pct),
        int(COR_ROXO_BRILHO[2] * alfa_pct),
        int(220 * alfa_pct)
    )

    s = (1.0 + math.sin(pulso * math.pi * 2) * 0.03) * ESCALA * 1.15

    base_w = 48 * s
    y_base = cy + 42 * s
    draw.line([cx - base_w, y_base, cx + base_w, y_base], fill=cor_linha, width=int(3.5 * s))
    draw.line([cx - base_w * 0.7, y_base - 4 * s, cx + base_w * 0.7, y_base - 4 * s], fill=cor_glow, width=int(2 * s))

    draw.line([cx, cy + 4 * s, cx, y_base], fill=cor_linha, width=int(4.5 * s))

    cup_r = 44 * s
    draw.arc([cx - cup_r, cy - 38 * s, cx + cup_r, cy + 14 * s], start=0, end=180, fill=cor_linha, width=int(4 * s))
    draw.line([cx - cup_r, cy - 12 * s, cx + cup_r, cy - 12 * s], fill=cor_glow, width=int(2.5 * s))

    pontos_serpente = []
    passos = 100
    for t in range(passos):
        frac = t / float(passos)
        sy = (y_base - 4 * s) - frac * (76 * s)
        sx = cx + math.sin(frac * math.pi * 3.6) * (20 * s)
        pontos_serpente.append((sx, sy))

    for i in range(len(pontos_serpente) - 1):
        draw.line([pontos_serpente[i], pontos_serpente[i + 1]], fill=cor_glow, width=int(4 * s))

    head_x = cx + 10 * s
    head_y = cy - 38 * s
    draw.ellipse([head_x - 6 * s, head_y - 5 * s, head_x + 6 * s, head_y + 5 * s], fill=cor_linha)
    draw.ellipse([head_x - 1 * s, head_y - 2 * s, head_x + 2 * s, head_y + 1 * s], fill=COR_CYAN)

    for sinal in [-1, 1]:
        mx = cx + sinal * 115 * s
        my = cy - 8 * s
        draw.ellipse([mx - 7 * s, my - 7 * s, mx + 7 * s, my + 7 * s], outline=cor_linha, width=int(1.8 * s))
        draw.line([cx + sinal * (cup_r + 6 * s), cy - 10 * s, mx - sinal * 8 * s, my], fill=cor_glow, width=int(1.2 * s))


def desenhar_ecg(draw, cx, cy, progresso, alfa_pct=1.0):
    if alfa_pct <= 0:
        return
    cor_ecg = (
        int(COR_ROXO[0] * alfa_pct),
        int(COR_ROXO[1] * alfa_pct),
        int(COR_ROXO[2] * alfa_pct),
        int(190 * alfa_pct)
    )
    y_base = cy + 68 * ESCALA
    x_inicio = cx - 140 * ESCALA
    x_fim = cx + 140 * ESCALA

    largura = x_fim - x_inicio
    pontos = []
    for x in range(int(x_inicio), int(x_fim), 2 * ESCALA):
        f = (x - x_inicio) / largura
        f_shift = (f - progresso) % 1.0
        y = y_base
        if 0.38 <= f_shift <= 0.42:
            y = y_base - 7 * ESCALA * math.sin((f_shift - 0.38) / 0.04 * math.pi)
        elif 0.42 < f_shift <= 0.46:
            y = y_base + 9 * ESCALA * math.sin((f_shift - 0.42) / 0.04 * math.pi)
        elif 0.46 < f_shift <= 0.52:
            y = y_base - 32 * ESCALA * math.sin((f_shift - 0.46) / 0.06 * math.pi)
        elif 0.52 < f_shift <= 0.57:
            y = y_base + 14 * ESCALA * math.sin((f_shift - 0.52) / 0.05 * math.pi)
        elif 0.57 < f_shift <= 0.65:
            y = y_base - 9 * ESCALA * math.sin((f_shift - 0.57) / 0.08 * math.pi)
        pontos.append((x, y))

    for i in range(len(pontos) - 1):
        draw.line([pontos[i], pontos[i + 1]], fill=cor_ecg, width=int(2 * ESCALA))


def desenhar_circuito_si(draw, cx, cy, alfa_pct=1.0, pulso=0.0):
    if alfa_pct <= 0:
        return

    cor_circuito = (
        int(COR_ROXO_CLARO[0] * alfa_pct),
        int(COR_ROXO_CLARO[1] * alfa_pct),
        int(COR_ROXO_CLARO[2] * alfa_pct),
        int(255 * alfa_pct)
    )
    cor_glow = (
        int(COR_ROXO_BRILHO[0] * alfa_pct),
        int(COR_ROXO_BRILHO[1] * alfa_pct),
        int(COR_ROXO_BRILHO[2] * alfa_pct),
        int(200 * alfa_pct)
    )

    s = ESCALA * 1.15

    r_orbit_x = 110 * s
    r_orbit_y = 44 * s
    ang_offset = pulso * math.pi * 2

    pontos_orb1 = []
    pontos_orb2 = []
    for a in range(0, 360, 6):
        rad = math.radians(a)
        ox = r_orbit_x * math.cos(rad)
        oy = r_orbit_y * math.sin(rad)

        rx1 = ox * math.cos(0.52) - oy * math.sin(0.52)
        ry1 = ox * math.sin(0.52) + oy * math.cos(0.52)
        pontos_orb1.append((cx + rx1, cy + ry1))

        rx2 = ox * math.cos(-0.52) - oy * math.sin(-0.52)
        ry2 = ox * math.sin(-0.52) + oy * math.cos(-0.52)
        pontos_orb2.append((cx + rx2, cy + ry2))

    pontos_orb1.append(pontos_orb1[0])
    pontos_orb2.append(pontos_orb2[0])
    for i in range(len(pontos_orb1) - 1):
        draw.line([pontos_orb1[i], pontos_orb1[i + 1]], fill=cor_glow, width=int(1.8 * s))
    for i in range(len(pontos_orb2) - 1):
        draw.line([pontos_orb2[i], pontos_orb2[i + 1]], fill=cor_glow, width=int(1.8 * s))

    for ang in [ang_offset, ang_offset + math.pi]:
        ox = r_orbit_x * math.cos(ang)
        oy = r_orbit_y * math.sin(ang)
        rx = ox * math.cos(0.52) - oy * math.sin(0.52)
        ry = ox * math.sin(0.52) + oy * math.cos(0.52)
        draw.ellipse([cx + rx - 5 * s, cy + ry - 5 * s, cx + rx + 5 * s, cy + ry + 5 * s], fill=cor_circuito)
        draw.ellipse([cx + rx - 2 * s, cy + ry - 2 * s, cx + rx + 2 * s, cy + ry + 2 * s], fill=COR_CYAN)

    chip_tam = 40 * s
    draw.rounded_rectangle(
        [cx - chip_tam, cy - chip_tam, cx + chip_tam, cy + chip_tam],
        radius=int(8 * s),
        outline=cor_circuito,
        width=int(3 * s),
        fill=(22, 27, 38, int(240 * alfa_pct))
    )

    vias = [
        (cx - chip_tam, cy - 18 * s, cx - chip_tam - 38 * s, cy - 18 * s),
        (cx - chip_tam, cy + 18 * s, cx - chip_tam - 30 * s, cy + 34 * s),
        (cx + chip_tam, cy - 18 * s, cx + chip_tam + 38 * s, cy - 18 * s),
        (cx + chip_tam, cy + 18 * s, cx + chip_tam + 30 * s, cy + 34 * s),
        (cx - 18 * s, cy - chip_tam, cx - 18 * s, cy - chip_tam - 26 * s),
        (cx + 18 * s, cy - chip_tam, cx + 18 * s, cy - chip_tam - 26 * s),
        (cx - 18 * s, cy + chip_tam, cx - 18 * s, cy + chip_tam + 26 * s),
        (cx + 18 * s, cy + chip_tam, cx + 18 * s, cy + chip_tam + 26 * s),
    ]
    for x1, y1, x2, y2 in vias:
        draw.line([x1, y1, x2, y2], fill=cor_circuito, width=int(2 * s))
        draw.ellipse([x2 - 3 * s, y2 - 3 * s, x2 + 3 * s, y2 + 3 * s], fill=cor_circuito)

    tag_texto = "</>"
    caixa = draw.textbbox((0, 0), tag_texto, font=fonte_code)
    tw = caixa[2] - caixa[0]
    th = caixa[3] - caixa[1]
    draw.text((cx - tw / 2, cy - th / 2 - 3 * s), tag_texto, font=fonte_code, fill=cor_circuito)


def desenhar_particulas_transicao(draw, cx, cy, t_pct):
    s = ESCALA
    rng_offset = int(t_pct * 30)
    bits = ["0", "1", "0", "1", "1", "0", "1", "0"]
    for i in range(28):
        ang = (i * 13 + rng_offset * 14) * math.pi / 180.0
        dist = (35 + (i * 9 + rng_offset * 7) % 95) * s
        px = cx + math.cos(ang) * dist
        py = cy + math.sin(ang) * dist * 0.75

        opac = int(210 * math.sin(t_pct * math.pi))
        cor_p = (COR_ROXO_CLARO[0], COR_ROXO_CLARO[1], COR_ROXO_CLARO[2], opac)

        char = bits[i % len(bits)]
        draw.text((px, py), char, font=fonte_bits, fill=cor_p)


def desenhar_healthtech_core(draw, cx, cy, alfa_pct=1.0, pulso=0.0):
    if alfa_pct <= 0:
        return
    s = ESCALA * 1.15
    cor_h = (
        int(COR_ROXO_CLARO[0] * alfa_pct),
        int(COR_ROXO_CLARO[1] * alfa_pct),
        int(COR_ROXO_CLARO[2] * alfa_pct),
        int(255 * alfa_pct)
    )
    cor_glow = (
        int(COR_ROXO_BRILHO[0] * alfa_pct),
        int(COR_ROXO_BRILHO[1] * alfa_pct),
        int(COR_ROXO_BRILHO[2] * alfa_pct),
        int(200 * alfa_pct)
    )

    raio = (48 + math.sin(pulso * math.pi * 2) * 4) * s
    pontos_hex = []
    for i in range(6):
        a = i * (math.pi / 3)
        pontos_hex.append((cx + raio * math.cos(a), cy + raio * math.sin(a)))
    for i in range(6):
        draw.line([pontos_hex[i], pontos_hex[(i + 1) % 6]], fill=cor_h, width=int(3 * s))
        vx, vy = pontos_hex[i]
        draw.ellipse([vx - 4 * s, vy - 4 * s, vx + 4 * s, vy + 4 * s], fill=cor_h)

    raio_interno = raio * 0.75
    for i in range(12):
        a = i * (math.pi / 6)
        px = cx + raio_interno * math.cos(a)
        py = cy + raio_interno * math.sin(a)
        draw.ellipse([px - 2 * s, py - 2 * s, px + 2 * s, py + 2 * s], fill=cor_glow)

    cw = 13 * s
    cl = 34 * s
    draw.rounded_rectangle([cx - cw, cy - cl, cx + cw, cy + cl], radius=int(4 * s), fill=cor_h)
    draw.rounded_rectangle([cx - cl, cy - cw, cx + cl, cy + cw], radius=int(4 * s), fill=cor_h)

    draw.ellipse([cx - 5 * s, cy - 5 * s, cx + 5 * s, cy + 5 * s], fill=(22, 27, 38, 255))
    draw.ellipse([cx - 3 * s, cy - 3 * s, cx + 3 * s, cy + 3 * s], fill=COR_CYAN)


def aplicar_brilho(img, t):
    pulso = 0.5 + 0.5 * math.sin(t * math.pi * 2)
    d = int((250 + 14 * pulso) * ESCALA)
    grad = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)
    alfa = grad.point(lambda v: max(0, int((1 - min(1.0, v / 179.0)) ** 1.8 * (70 + 20 * pulso))))
    cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    brilho = Image.new("RGBA", (d, d), COR_ROXO_PROFUNDO[:3] + (0,))
    brilho.putalpha(alfa)
    cam.paste(brilho, (CX - d // 2, CY - d // 2))
    img.alpha_composite(cam)


def salvar_gif(frames, caminho, duracao):
    n = len(frames)
    passo = max(1, n // 12)
    amostras = frames[::passo][:12]
    folha = Image.new("RGB", (SAIDA_LARGURA, SAIDA_ALTURA * len(amostras)))
    for i, fr in enumerate(amostras):
        folha.paste(fr, (0, i * SAIDA_ALTURA))
    pal = folha.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    paleta = (pal.getpalette() + [0] * 768)[:768]
    transp = 255

    quant = []
    for fr in frames:
        q = fr.quantize(palette=pal, dither=Image.Dither.NONE)
        q.putpalette(paleta)
        quant.append(q)

    saida = [quant[0]]
    recon = quant[0].convert("RGB")
    for i in range(1, n):
        dr, dg, db = ImageChops.difference(frames[i], recon).split()
        diff = ImageChops.lighter(dr, ImageChops.lighter(dg, db))
        igual = diff.point(lambda v: 255 if v <= 4 else 0)
        fr = quant[i].copy()
        fr.paste(transp, mask=igual)
        fr.info["transparency"] = transp
        saida.append(fr)
        recon = Image.composite(recon, quant[i].convert("RGB"), igual)

    saida[0].save(caminho, save_all=True, append_images=saida[1:], loop=0,
                  duration=duracao, optimize=False, disposal=1, transparency=transp)


def gerar_animacao():
    print("Iniciando geração dos frames da animação puramente visual...")
    frames = []

    TOTAL_FRAMES = 60

    for f in range(TOTAL_FRAMES):
        img = Image.new("RGBA", (W, H), BG_COLOR)
        aplicar_brilho(img, f / TOTAL_FRAMES)
        draw = ImageDraw.Draw(img)
        desenhar_card_base(draw)

        if f <= 18:
            t = f / 18.0
            desenhar_taca_higia(draw, CX, CY, alfa_pct=1.0, pulso=t)
            desenhar_ecg(draw, CX, CY, progresso=t, alfa_pct=0.95)

        elif 19 <= f <= 27:
            t = (f - 19) / 8.0
            alfa_farm = max(0.0, 1.0 - t * 1.5)
            alfa_si = max(0.0, (t - 0.3) * 1.4)
            desenhar_taca_higia(draw, CX, CY, alfa_pct=alfa_farm)
            desenhar_circuito_si(draw, CX, CY, alfa_pct=alfa_si, pulso=t)
            desenhar_particulas_transicao(draw, CX, CY, t_pct=t)

        elif 28 <= f <= 45:
            t = (f - 28) / 17.0
            desenhar_circuito_si(draw, CX, CY, alfa_pct=1.0, pulso=t)

        elif 46 <= f <= 53:
            t = (f - 46) / 7.0
            alfa_si = max(0.0, 1.0 - t * 1.4)
            alfa_ht = max(0.0, (t - 0.2) * 1.3)
            desenhar_circuito_si(draw, CX, CY, alfa_pct=alfa_si, pulso=t)
            desenhar_healthtech_core(draw, CX, CY, alfa_pct=alfa_ht, pulso=t)
            desenhar_particulas_transicao(draw, CX, CY, t_pct=t)

        else:
            t = (f - 54) / 6.0
            alfa_ht = max(0.0, 1.0 - t)
            alfa_loop = t
            desenhar_healthtech_core(draw, CX, CY, alfa_pct=alfa_ht, pulso=t)
            if alfa_loop > 0.3:
                desenhar_taca_higia(draw, CX, CY, alfa_pct=alfa_loop * 0.8)

        img_redimensionada = img.resize((SAIDA_LARGURA, SAIDA_ALTURA), Image.Resampling.LANCZOS)
        frames.append(img_redimensionada.convert("RGB"))

    print(f"Salvando GIF em: {ARQUIVO_SAIDA}")
    salvar_gif(frames, ARQUIVO_SAIDA, duracao=70)
    tamanho_kb = os.path.getsize(ARQUIVO_SAIDA) / 1024
    print(f"Novo GIF gerado com sucesso! Tamanho: {tamanho_kb:.1f} KB (Apenas visual, sem texto).")


if __name__ == "__main__":
    gerar_animacao()
