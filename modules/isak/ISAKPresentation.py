from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import streamlit as st


# ============================================================
# MODELOS DE PRESENTACIÓN (OUTPUT ONLY)
# ============================================================

@dataclass(frozen=True)
class PresentacionItem:
    label: str
    value: Optional[float]
    unit: str = ""
    z: Optional[float] = None


@dataclass(frozen=True)
class PresentacionBloque:
    titulo: str
    items: List[PresentacionItem]


# ============================================================
# ISAK PRESENTATION
# ============================================================

class ISAKPresentation:
    """
    Capa de presentación ISAK.

    - Replica la hoja PRESENTATION del Excel
    - NO calcula
    - NO valida
    - NO interpreta
    - NO semáforos
    - SOLO organiza y muestra datos
    """

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    @staticmethod
    def _f(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _z(z_raw: Dict[str, float], key: str) -> Optional[float]:
        try:
            return float(z_raw.get(key))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _z_raw(record: Dict[str, Any]) -> Dict[str, float]:
        return record.get("calculos", {}).get("z_raw", {}) or {}

    @staticmethod
    def _fmt_value(v: Optional[float], unit: str = "", decimals: int = 2) -> str:
        if v is None:
            return "—"
        s = f"{v:.{decimals}f}"
        if unit:
            s = f"{s} {unit}"
        return s

    # --------------------------------------------------------
    # BLOQUES ISAK (RAW + Z)
    # --------------------------------------------------------

    @classmethod
    def _bloque_basicos(cls, r: Dict[str, Any]) -> PresentacionBloque:
        z = cls._z_raw(r)
        return PresentacionBloque(
            titulo="Datos básicos",
            items=[
                PresentacionItem("Peso", cls._f(r.get("peso_bruto_kg")), "kg", cls._z(z, "peso_bruto_kg")),
                # Talla corporal suele ser referencia Phantom (no z en tu z_raw)
                PresentacionItem("Talla corporal", cls._f(r.get("talla_corporal_cm")), "cm", cls._z(z, "talla_corporal_cm")),
                PresentacionItem("Talla sentado", cls._f(r.get("talla_sentado_cm")), "cm", cls._z(z, "talla_sentado_cm")),
                PresentacionItem("Envergadura", cls._f(r.get("envergadura_cm")), "cm", cls._z(z, "envergadura_cm")),
            ],
        )

    @classmethod
    def _bloque_longitudes(cls, r: Dict[str, Any]) -> PresentacionBloque:
        z = cls._z_raw(r)
        return PresentacionBloque(
            titulo="Longitudes y segmentos (cm)",
            items=[
                PresentacionItem("Acromial - Radial", cls._f(r.get("acromial_radial")), "cm", cls._z(z, "acromial_radial")),
                PresentacionItem("Radial - Estiloidea", cls._f(r.get("radial_estiloidea")), "cm", cls._z(z, "radial_estiloidea")),
                PresentacionItem("Medial estiloidea - dactilar", cls._f(r.get("medial_estiloidea_dactilar")), "cm", cls._z(z, "medial_estiloidea_dactilar")),
                PresentacionItem("Ilioespinal", cls._f(r.get("ilioespinal")), "cm", cls._z(z, "ilioespinal")),
                PresentacionItem("Trocantérea", cls._f(r.get("trocanterea")), "cm", cls._z(z, "trocanterea")),
                PresentacionItem("Trocantérea - tibial lateral", cls._f(r.get("troc_tibial_lateral")), "cm", cls._z(z, "troc_tibial_lateral")),
                PresentacionItem("Tibial lateral", cls._f(r.get("tibial_lateral")), "cm", cls._z(z, "tibial_lateral")),
                PresentacionItem("Tibial medial - maleolar medial", cls._f(r.get("tibial_medial_maleolar_medial")), "cm", cls._z(z, "tibial_medial_maleolar_medial")),
                PresentacionItem("Pie", cls._f(r.get("pie")), "cm", cls._z(z, "pie")),
            ],
        )

    @classmethod
    def _bloque_diametros(cls, r: Dict[str, Any]) -> PresentacionBloque:
        z = cls._z_raw(r)
        return PresentacionBloque(
            titulo="Diámetros óseos (cm)",
            items=[
                PresentacionItem("Biacromial", cls._f(r.get("biacromial")), "cm", cls._z(z, "biacromial")),
                PresentacionItem("Tórax transverso", cls._f(r.get("torax_transverso")), "cm", cls._z(z, "torax_transverso")),
                PresentacionItem("Tórax antero-posterior", cls._f(r.get("torax_antero_posterior")), "cm", cls._z(z, "torax_antero_posterior")),
                PresentacionItem("Bi-iliocrestídeo", cls._f(r.get("bi_iliocrestideo")), "cm", cls._z(z, "bi_iliocrestideo")),
                PresentacionItem("Humeral (biepicondilar)", cls._f(r.get("humeral_biepicondilar")), "cm", cls._z(z, "humeral_biepicondilar")),
                PresentacionItem("Femoral (biepicondilar)", cls._f(r.get("femoral_biepicondilar")), "cm", cls._z(z, "femoral_biepicondilar")),
                PresentacionItem("Muñeca (biestiloideo)", cls._f(r.get("muneca_biestiloideo")), "cm", cls._z(z, "muneca_biestiloideo")),
                PresentacionItem("Tobillo (bimaleolar)", cls._f(r.get("tobillo_bimaleolar")), "cm", cls._z(z, "tobillo_bimaleolar")),
                PresentacionItem("Mano", cls._f(r.get("mano")), "cm", cls._z(z, "mano")),
            ],
        )

    @classmethod
    def _bloque_perimetros(cls, r: Dict[str, Any]) -> PresentacionBloque:
        z = cls._z_raw(r)
        return PresentacionBloque(
            titulo="Perímetros corporales (cm)",
            items=[
                PresentacionItem("Cabeza", cls._f(r.get("perimetro_cabeza")), "cm", cls._z(z, "perimetro_cabeza")),
                PresentacionItem("Cuello", cls._f(r.get("perimetro_cuello")), "cm", cls._z(z, "perimetro_cuello")),
                PresentacionItem("Brazo relajado", cls._f(r.get("perimetro_brazo_relajado")), "cm", cls._z(z, "perimetro_brazo_relajado")),
                PresentacionItem("Brazo flexionado en tensión", cls._f(r.get("perimetro_brazo_flexionado_en_tension")), "cm", cls._z(z, "perimetro_brazo_flexionado_en_tension")),
                PresentacionItem("Antebrazo máximo", cls._f(r.get("perimetro_antebrazo_maximo")), "cm", cls._z(z, "perimetro_antebrazo_maximo")),
                PresentacionItem("Muñeca", cls._f(r.get("perimetro_muneca")), "cm", cls._z(z, "perimetro_muneca")),
                PresentacionItem("Tórax", cls._f(r.get("perimetro_torax_mesoesternal")), "cm", cls._z(z, "perimetro_torax_mesoesternal")),
                PresentacionItem("Cintura (min)", cls._f(r.get("perimetro_cintura_minima")), "cm", cls._z(z, "perimetro_cintura_minima")),
                PresentacionItem("Abdominal (max)", cls._f(r.get("perimetro_abdominal_maxima")), "cm", cls._z(z, "perimetro_abdominal_maxima")),
                PresentacionItem("Caderas (max)", cls._f(r.get("perimetro_cadera_maximo")), "cm", cls._z(z, "perimetro_cadera_maximo")),
                PresentacionItem("Muslo (max)", cls._f(r.get("perimetro_muslo_maximo")), "cm", cls._z(z, "perimetro_muslo_maximo")),
                PresentacionItem("Muslo medial", cls._f(r.get("perimetro_muslo_medial")), "cm", cls._z(z, "perimetro_muslo_medial")),
                PresentacionItem("Pantorrilla (max)", cls._f(r.get("perimetro_pantorrilla_maxima")), "cm", cls._z(z, "perimetro_pantorrilla_maxima")),
                PresentacionItem("Tobillo (max)", cls._f(r.get("perimetro_tobillo_minima")), "cm", cls._z(z, "perimetro_tobillo_minima")),
            ],
        )

    @classmethod
    def _bloque_pliegues(cls, r: Dict[str, Any]) -> PresentacionBloque:
        z = cls._z_raw(r)
        return PresentacionBloque(
            titulo="Pliegues cutáneos (mm)",
            items=[
                PresentacionItem("Tríceps", cls._f(r.get("pliegue_triceps")), "mm", cls._z(z, "pliegue_triceps")),
                PresentacionItem("Subescapular", cls._f(r.get("pliegue_subescapular")), "mm", cls._z(z, "pliegue_subescapular")),
                PresentacionItem("Bíceps", cls._f(r.get("pliegue_biceps")), "mm", cls._z(z, "pliegue_biceps")),
                PresentacionItem("Cresta ilíaca", cls._f(r.get("pliegue_cresta_iliaca")), "mm", cls._z(z, "pliegue_cresta_iliaca")),
                PresentacionItem("Supraespinal", cls._f(r.get("pliegue_supraespinal")), "mm", cls._z(z, "pliegue_supraespinal")),
                PresentacionItem("Abdominal", cls._f(r.get("pliegue_abdominal")), "mm", cls._z(z, "pliegue_abdominal")),
                PresentacionItem("Muslo frontal", cls._f(r.get("pliegue_muslo_frontal")), "mm", cls._z(z, "pliegue_muslo_frontal")),
                PresentacionItem("Pantorrilla", cls._f(r.get("pliegue_pantorrilla_maxima")), "mm", cls._z(z, "pliegue_pantorrilla_maxima")),
                PresentacionItem("Antebrazo", cls._f(r.get("pliegue_antebrazo")), "mm", cls._z(z, "pliegue_antebrazo")),
            ],
        )

    @classmethod
    def _bloque_resumen(cls, record: Dict[str, Any]) -> PresentacionBloque:
        c = record.get("calculos", {}) or {}

        mo = None
        try:
            mm = c.get("ajuste_muscular", {}).get("masa_ajustada_kg")
            mo_ = c.get("ajuste_osea", {}).get("masa_ajustada_kg")
            if mm is not None and mo_ is not None and float(mo_) != 0:
                mo = float(mm) / float(mo_)
        except Exception:
            mo = None

        return PresentacionBloque(
            titulo="Resumen",
            items=[
                PresentacionItem("Peso", cls._f(record.get("peso_bruto_kg")), "kg"),
                PresentacionItem("Talla", cls._f(record.get("talla_corporal_cm")), "cm"),
                PresentacionItem("Suma de 6 pliegues", cls._f(c.get("suma_6_pliegues_mm")), "mm"),
                PresentacionItem("% Grasa", cls._f(c.get("ajuste_adiposa", {}).get("pct")), "%"),
                PresentacionItem("% Muscular", cls._f(c.get("ajuste_muscular", {}).get("pct")), "%"),
                PresentacionItem("Masa ósea", cls._f(c.get("ajuste_osea", {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Índice músculo/óseo", cls._f(mo), ""),
            ],
        )

    # -----------------------------
    # FRACCIONAMIENTO 5 COMPONENTES (KERR)
    # -----------------------------

    @classmethod
    def _bloque_fraccionamiento(cls, c: Dict[str, Any]) -> PresentacionBloque:
        return PresentacionBloque(
            titulo="Fraccionamiento 5 componentes (D. Kerr, 1988)",
            items=[
                PresentacionItem("Masa adiposa (%)", cls._f((c.get("ajuste_adiposa") or {}).get("pct")), "%"),
                PresentacionItem("Masa adiposa (kg)", cls._f((c.get("ajuste_adiposa") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Masa muscular (%)", cls._f((c.get("ajuste_muscular") or {}).get("pct")), "%"),
                PresentacionItem("Masa muscular (kg)", cls._f((c.get("ajuste_muscular") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Masa residual (%)", cls._f((c.get("ajuste_residual") or {}).get("pct")), "%"),
                PresentacionItem("Masa residual (kg)", cls._f((c.get("ajuste_residual") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Masa ósea (%)", cls._f((c.get("ajuste_osea") or {}).get("pct")), "%"),
                PresentacionItem("Masa ósea (kg)", cls._f((c.get("ajuste_osea") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Masa de la piel (%)", cls._f((c.get("ajuste_piel") or {}).get("pct")), "%"),
                PresentacionItem("Masa de la piel (kg)", cls._f((c.get("ajuste_piel") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Masa total (%)", cls._f((c.get("ajuste_peso_estructurado") or {}).get("pct")), "%"),
                PresentacionItem("Masa total (kg)", cls._f((c.get("ajuste_peso_estructurado") or {}).get("masa_ajustada_kg")), "kg"),
                PresentacionItem("Diferencia % peso estructurado - peso bruto", cls._f(c.get("diferencia_peso_pct")), "%"),
            ],
        )

    # --------------------------------------------------------
    # RENDER GENÉRICO: BLOQUES SIMPLES (RAW + Z)
    # --------------------------------------------------------

    @classmethod
    def render_bloque_simple(cls, bloque: PresentacionBloque):
        """
        Renderiza un bloque ISAK simple en formato tabla
        con cabecera de columnas: Componente | Valor | Z-score
        """

        st.subheader(bloque.titulo, divider="red")

        # Header estilo Excel
        h1, h2, h3= st.columns([7, 1, 1])
        h1.markdown("**Componente**")
        h2.markdown("**Valor**")
        h3.markdown("**Z-score**")

        for item in bloque.items:
            c1, c2, c3 = st.columns([7, 1, 1])
            c1.markdown(f"**{item.label}**")

            c2.write(cls._fmt_value(item.value, unit=item.unit, decimals=2))
            c3.write("—" if item.z is None else f"{item.z:.2f}")

    # --------------------------------------------------------
    # RENDER ESPECIAL: FRACCIONAMIENTO 5 COMPONENTES (KERR)
    # --------------------------------------------------------

    @classmethod
    def render_fraccionamiento_5_componentes(cls, calculos: dict):
        """
        Renderiza el fraccionamiento 5 componentes (D. Kerr, 1988)
        en formato tabla, una fila por componente,
        con % y kg en la misma línea (estilo Excel).
        Incluye Z-score cuando exista.
        La columna Dif intenta mostrar (ajustado - bruto) si hay masa bruta disponible.
        """
        c = calculos or {}

        def _dif(ajustado: Any, bruto: Any) -> Optional[float]:
            a = cls._f(ajustado)
            b = cls._f(bruto)
            if a is None or b is None:
                return None
            return a - 0

        filas = [
            (
                "1 - Masa Adiposa",
                (c.get("ajuste_adiposa") or {}).get("pct"),
                (c.get("ajuste_adiposa") or {}).get("masa_ajustada_kg"),
                c.get("z_adiposa"),
                _dif((c.get("ajuste_adiposa") or {}).get("masa_ajustada_kg"), c.get("masa_adiposa_kg")),
            ),
            (
                "2 - Masa Muscular",
                (c.get("ajuste_muscular") or {}).get("pct"),
                (c.get("ajuste_muscular") or {}).get("masa_ajustada_kg"),
                c.get("z_muscular"),
                _dif((c.get("ajuste_muscular") or {}).get("masa_ajustada_kg"), c.get("masa_muscular_kg")),
            ),
            (
                "3 - Masa Residual",
                (c.get("ajuste_residual") or {}).get("pct"),
                (c.get("ajuste_residual") or {}).get("masa_ajustada_kg"),
                c.get("z_residual"),
                _dif((c.get("ajuste_residual") or {}).get("masa_ajustada_kg"), c.get("masa_residual_kg")),
            ),
            (
                "4 - Masa Ósea",
                (c.get("ajuste_osea") or {}).get("pct"),
                (c.get("ajuste_osea") or {}).get("masa_ajustada_kg"),
                c.get("z_osea"),
                _dif((c.get("ajuste_osea") or {}).get("masa_ajustada_kg"), c.get("masa_osea_kg")),
            ),
            (
                "5 - Masa de la Piel",
                (c.get("ajuste_piel") or {}).get("pct"),
                (c.get("ajuste_piel") or {}).get("masa_ajustada_kg"),
                None,
                _dif((c.get("ajuste_piel") or {}).get("masa_ajustada_kg"), c.get("masa_piel_kg")),
            ),
            (
                "6 - Masa Total",
                (c.get("ajuste_peso_estructurado") or {}).get("pct"),
                (c.get("ajuste_peso_estructurado") or {}).get("masa_ajustada_kg"),
                (((c.get("ajuste_peso_estructurado") or {}).get("ajuste_alometrico") - 64.58) / 8.6),
                _dif((c.get("ajuste_peso_estructurado") or {}).get("masa_ajustada_kg"), c.get("peso_estructurado_kg")),
            ),
        ]

        st.subheader("Fraccionamiento 5 componentes (D. Kerr, 1988)", divider="red")

        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 2])
        h1.markdown("**Componente**")
        h2.markdown("**Porcentaje**")
        h3.markdown("**Kg**")
        h4.markdown("**Score-Z**")
        h5.markdown("**Dif.**")

        for nombre, pct, kg, z, dif in filas:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])

            c1.write(nombre)
            c2.write("—" if pct is None else f"{float(pct):.2f} %")
            c3.write("—" if kg is None else f"{float(kg):.3f}")
            c4.write("—" if z is None else f"{float(z):.2f}")
            c5.write("—" if dif is None else f"{float(dif):.3f}")

        if c.get("diferencia_peso_pct") is not None:
            st.markdown(
                f"**Porcentaje de diferencia Peso Estructurado - Peso Bruto:** "
                f"{float(c['diferencia_peso_pct']):.2f} %"
            )

    @classmethod
    def render_resumen(cls, record: Dict[str, Any]):
        """
        Renderiza el RESUMEN ISAK en una sola fila,
        con múltiples columnas (estilo Excel).
        NO incluye Z-score.
        """

        c = record.get("calculos", {}) or {}

        # # Cálculo seguro del índice músculo / óseo
        # idx_mo = None
        # try:
        #     mm = c.get("ajuste_muscular", {}).get("masa_ajustada_kg")
        #     mo = c.get("ajuste_osea", {}).get("masa_ajustada_kg")
        #     if mm is not None and mo not in (None, 0):
        #         idx_mo = float(mm) / float(mo)
        # except Exception:
        #     idx_mo = None

        st.subheader("Resumen", divider="red")

        # Cabecera tipo Excel
        h1, h2, h3, h4, h5, h6, h7 = st.columns([2, 2, 2, 2, 2, 2, 2])

        h1.markdown("**Peso (kg)**")
        h2.markdown("**Talla (cm)**")
        h3.markdown("**Σ 6 Pliegues (mm)**")
        h4.markdown("**% Grasa**")
        h5.markdown("**% Muscular**")
        h6.markdown("**Masa ósea (kg)**")
        h7.markdown("**Índice M/O**")

        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2, 2, 2, 2, 2, 2])

        c1.write("—" if record.get("peso_bruto_kg") is None else f"{record['peso_bruto_kg']:.2f}")
        c2.write("—" if record.get("talla_corporal_cm") is None else f"{record['talla_corporal_cm']:.2f}")
        c3.write("—" if c.get("suma_6_pliegues_mm") is None else f"{c['suma_6_pliegues_mm']:.2f}")
        c4.write("—" if c.get("ajuste_adiposa", {}).get("pct") is None else f"{c['ajuste_adiposa']['pct']:.2f}")
        c5.write("—" if c.get("ajuste_muscular", {}).get("pct") is None else f"{c['ajuste_muscular']['pct']:.2f}")
        c6.write("—" if c.get("ajuste_osea", {}).get("masa_ajustada_kg") is None else f"{c['ajuste_osea']['masa_ajustada_kg']:.2f}")
        c7.write("—" if c.get("idx_musculo_oseo") is None else f"{c['idx_musculo_oseo']:.2f}")

    # --------------------------------------------------------
    # API PÚBLICA
    # --------------------------------------------------------

    @classmethod
    def build(cls, record: Dict[str, Any]) -> List[PresentacionBloque]:
        """
        Devuelve la estructura FINAL de presentación ISAK,
        en el mismo orden que la hoja PRESENTATION del Excel.
        """
        return [
            cls._bloque_basicos(record),
            cls._bloque_longitudes(record),
            cls._bloque_diametros(record),
            cls._bloque_perimetros(record),
            cls._bloque_pliegues(record)
        ]
