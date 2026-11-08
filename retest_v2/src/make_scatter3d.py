"""3D and 2D scatter of REAL D1 test-split features (chatbot_figures/d1_test_features.csv). Reviewed rewrite of the chatbot script prompt1_plotly_3d.py:
reads the CSV only, drops rows with empty E_sup (ABSTAIN) and prints the count, no jitter/sampling/imputation, title numbers computed from the data.
Usage: make_scatter3d.py"""
import os

import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
CSV = os.path.join(RT, "chatbot_figures", "d1_test_features.csv")
OUT = os.path.join(RT, "results", "figures")
FONT = "DejaVu Sans, Arial, sans-serif"
COPY_COL, NOT_COL = "#D55E00", "#0072B2"        # colour-blind-safe pair; markers also differ (circle / diamond)
AXES = [("cosine", "Embedding cosine (A vs B)"), ("E_sup", "E_sup: support excess (A source minus B source)"), ("S_disguise", "S_disguise: semantic-lexical contrast")]


def load():
    raw = pd.read_csv(CSV)
    df = raw.dropna(subset=["E_sup"]).copy()
    print("rows read %d, dropped (E_sup empty = ABSTAIN) %d, plotted n = %d" % (len(raw), len(raw) - len(df), len(df)))
    return df


def split(df):
    return df[df["copying_undisclosed"] == 1], df[df["copying_undisclosed"] == 0]


def title_for(df):
    a = {c: roc_auc_score(df["copying_undisclosed"], df[c]) for c, _ in AXES}
    return ("Undisclosed copying overlaps on cosine and separates on E_sup and S_disguise<br>"
            "<sup>D1 test split, n = %d; AUROC of each axis alone: cosine %.2f, E_sup %.2f, S_disguise %.2f</sup>" % (len(df), a["cosine"], a["E_sup"], a["S_disguise"]))


def trace3d(d, name, col, sym):
    return go.Scatter3d(x=d["cosine"], y=d["E_sup"], z=d["S_disguise"], mode="markers", name=name,
                        marker=dict(size=4.2, opacity=0.75, color=col, symbol=sym),
                        customdata=d[["type", "scenario_id", "replicate"]],
                        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} (rep %{customdata[2]})<br>cosine %{x:.3f}<br>E_sup %{y:.3f}<br>S_disguise %{z:.3f}<extra>" + name + "</extra>")


def axis3d(title):
    return dict(title=title, backgroundcolor="#ffffff", gridcolor="#d9d9d9", linecolor="#000000", showbackground=True,
                tickfont=dict(color="#000000", family=FONT, size=13), title_font=dict(color="#000000", family=FONT, size=14))


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load()
    dc, dn = split(df)
    print("class counts: copying %d, not copying %d" % (len(dc), len(dn)))
    title = title_for(df)
    fig = go.Figure([trace3d(dc, "undisclosed copying", COPY_COL, "circle"), trace3d(dn, "not copying", NOT_COL, "diamond")])
    fig.update_layout(title=dict(text=title, x=0.5, xanchor="center", font=dict(family=FONT, size=15, color="#000000")), font=dict(family=FONT, color="#000000"),
                      paper_bgcolor="#ffffff", margin=dict(l=10, r=10, t=90, b=10),
                      legend=dict(x=0.02, y=0.93, bgcolor="rgba(255,255,255,0.9)", bordercolor="#000000", borderwidth=1),
                      scene=dict(xaxis=axis3d("Cosine (A vs B)"), yaxis=axis3d("E_sup (support excess)"), zaxis=axis3d("S_disguise")))
    fig.write_html(os.path.join(OUT, "fig6_scatter3d.html"), include_plotlyjs="cdn", full_html=True)
    for k, eye in enumerate((dict(x=1.4, y=-1.4, z=1.0), dict(x=-1.5, y=-1.25, z=0.85), dict(x=0.0, y=-1.95, z=0.3)), 1):
        fig.update_layout(scene_camera=dict(eye=eye, center=dict(x=0, y=0, z=-0.12)))
        fig.write_image(os.path.join(OUT, "fig6_scatter3d_view%d.png" % k), width=1800, height=1200, scale=1)
    f2 = go.Figure([go.Scatter(x=d["cosine"], y=d["E_sup"], mode="markers", name=n, marker=dict(size=6, opacity=0.7, color=c, symbol=s))
                    for d, n, c, s in ((dc, "undisclosed copying", COPY_COL, "circle"), (dn, "not copying", NOT_COL, "diamond"))])
    f2.update_layout(title=dict(text=title, x=0.5, xanchor="center", font=dict(family=FONT, size=15, color="#000000")), font=dict(family=FONT, color="#000000"),
                     paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(l=80, r=40, t=100, b=70),
                     xaxis=dict(title=AXES[0][1], gridcolor="#e3e3e3", linecolor="#000000", mirror=True, ticks="outside", showline=True),
                     yaxis=dict(title=AXES[1][1], gridcolor="#e3e3e3", linecolor="#000000", mirror=True, ticks="outside", showline=True),
                     legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.9)", bordercolor="#000000", borderwidth=1))
    f2.write_image(os.path.join(OUT, "fig6_scatter2d_cosine_vs_esup.png"), width=1800, height=1200, scale=1)
    print("saved:", sorted(f for f in os.listdir(OUT) if f.startswith("fig6")))


if __name__ == "__main__":
    main()
