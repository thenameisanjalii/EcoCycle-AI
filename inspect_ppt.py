import pptx
from pptx import Presentation
import json

prs = Presentation(r"C:\Users\patid\Downloads\EcoCycle AI.pptx")

print("Slide width (inches):", prs.slide_width.inches, "height (inches):", prs.slide_height.inches)
print("Number of slides:", len(prs.slides))

info = []
for i, slide in enumerate(prs.slides):
    s_data = {
        "slide_number": i + 1,
        "shapes": []
    }
    for s_idx, shape in enumerate(slide.shapes):
        sh_data = {
            "index": s_idx,
            "name": shape.name,
            "type": str(shape.shape_type),
            "left_in": round(shape.left.inches, 2),
            "top_in": round(shape.top.inches, 2),
            "width_in": round(shape.width.inches, 2),
            "height_in": round(shape.height.inches, 2),
            "paragraphs": []
        }
        if shape.has_text_frame:
            for p_idx, p in enumerate(shape.text_frame.paragraphs):
                p_text = p.text.strip()
                if p_text:
                    runs_info = []
                    for r in p.runs:
                        color_str = None
                        try:
                            if r.font.color and r.font.color.rgb:
                                color_str = str(r.font.color.rgb)
                        except:
                            pass
                        runs_info.append({
                            "text": r.text,
                            "font": r.font.name,
                            "size": r.font.size.pt if r.font.size else None,
                            "bold": r.font.bold,
                            "color": color_str
                        })
                    sh_data["paragraphs"].append({
                        "p_idx": p_idx,
                        "text": p.text,
                        "level": p.level,
                        "runs": runs_info
                    })
        elif shape.has_table:
            table_data = []
            for row in shape.table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_data.append(row_cells)
            sh_data["table"] = table_data
        s_data["shapes"].append(sh_data)
    info.append(s_data)

with open("ppt_full_analysis.json", "w", encoding="utf-8") as f:
    json.dump(info, f, indent=2, ensure_ascii=False)

print("Saved detailed analysis to ppt_full_analysis.json")
