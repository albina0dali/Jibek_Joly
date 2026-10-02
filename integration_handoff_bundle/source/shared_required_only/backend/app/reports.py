import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from xml.sax.saxutils import escape


def clock(seconds):
    return f'{8+int(seconds)//3600:02}:{int(seconds)%3600//60:02}:{int(seconds)%60:02}'


def csv_report(snapshot):
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(['category','id','status_or_score','delay_seconds_or_weight','detail'])
    for t in snapshot['trains']:
        writer.writerow(['train',t['id'],t['status'],t['delay_seconds'],f'{t["distance_km"]} km; {t["speed_kmh"]} km/h'])
    for i in snapshot['incidents']:
        writer.writerow(['incident',i['id'],i['status'],i['delay_seconds'],f'{i["type"]} at {i["location_id"]}'])
    for c in snapshot['conflicts']+snapshot.get('resolved_conflicts',[]):
        writer.writerow(['conflict',c['id'],c['status'],c['predicted_delay'],c['description']])
    for q in snapshot['quality']['components']:
        writer.writerow(['quality',q['name'],q['score'],q['weight'],f'{q["contribution"]} points; {q["reason"]}'])
    return output.getvalue()


def pdf_report(snapshot, actions, history):
    output=io.BytesIO()
    doc=SimpleDocTemplate(output,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=32,bottomMargin=32)
    styles=getSampleStyleSheet()
    items=[]
    def paragraph(text,style='BodyText'):
        items.append(Paragraph(escape(text),styles[style]))
        items.append(Spacer(1,8))
    paragraph('Autodispatcher Demo Report','Title')
    paragraph(f'Synthetic advisory simulation | {clock(history[0]["time"] if history else snapshot["time"])} - {clock(snapshot["time"])} | Asia/Qyzylorda')
    paragraph(f'Quality Index: {snapshot["quality"]["value"]} / 100 ({snapshot["quality"]["category"]})','Heading2')
    paragraph(f'Total projected delay: {sum(t["delay_seconds"] for t in snapshot["trains"])/60:.1f} min. Hard conflicts: {len(snapshot["conflicts"])}. Selected recommendation: {snapshot["selected_recommendation"] or "Baseline schedule"}.')
    rows=[['Train','Type','State','Delay (min)','Arrival']]+[[t['id'],t['type'],t['status'],f'{t["delay_seconds"]/60:.1f}',clock(t['eta'])] for t in snapshot['trains']]
    table=Table(rows,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#182b3a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]))
    items.extend([table,Spacer(1,12)])
    paragraph('Quality breakdown','Heading2')
    for q in snapshot['quality']['components']:
        paragraph(f'{q["name"].title()}: score {q["score"]}, weight {q["weight"]}%, contribution {q["contribution"]}. {q["reason"]}')
    paragraph('Incidents & replanning actions','Heading2')
    for i in snapshot['incidents']:
        paragraph(f'{i["id"]}: {i["type"]} at {i["location_id"]}, {i["status"]}, duration {i["expected_duration"]/60:.0f} min')
    for a in reversed(actions[:12]):
        paragraph(f'{clock(a["time"])} - {a["description"]}')
    paragraph('Decision-support prototype. Fictional data only. Recommendations apply to the simulator and do not control railway infrastructure.')
    doc.build(items)
    return output.getvalue()
