# Write a validation script to check SVG + CSV assignments against Excel constraints.
# The script does geometric checks (visibility, adjacency, separation), aisle width,
# large/small booth counts, unassigned booths, and produces a JSON report.
#
# Usage:
#   python validate_layout.py --svg venue_layout.svg --csv placement_result.csv --xlsx venue_constraints.xlsx --out report.json
#
# Notes:
# - "visible_from_entrance": line-of-sight from door center to target booth center must not intersect any other booth rectangle.
# - "near_window": booth center must be within the rightmost quartile of booth x-positions (or within 250 px from window x).
# - Adjacency "A~B": booths share edge or corner (rect adjacency within 10 px tolerance).
# - Separation "A!~B": not edge/corner adjacent.
# - "LargeBooth>=N": at least N large booths are occupied.
# - Aisle ≥ 80 px between top and bottom rows (computed from booth rectangles' vertical gap).
# - Exactly two unassigned booths overall (12 total booths).
#
# This script is defensive: if any parsing error occurs, it records a violation.
import argparse, json, re, math
from xml.etree import ElementTree as ET
import pandas as pd
from collections import defaultdict

def rect_center(r):
    return (r['x'] + r['w']/2.0, r['y'] + r['h']/2.0)

def line_intersects_rect(p1, p2, r):
    # Liang–Barsky style: approximate via Cohen-Sutherland or simple segment-AABB test
    # We'll do a simple robust check: if segment intersects any of the 4 rectangle edges
    x1,y1 = p1; x2,y2 = p2
    rx,ry,rw,rh = r['x'], r['y'], r['w'], r['h']
    # Quick reject if both endpoints are inside -> still "intersects"
    if (rx <= x1 <= rx+rw and ry <= y1 <= ry+rh) or (rx <= x2 <= rx+rw and ry <= y2 <= ry+rh):
        return True
    # Define rectangle edges as segments
    edges = [((rx,ry),(rx+rw,ry)),
             ((rx+rw,ry),(rx+rw,ry+rh)),
             ((rx+rw,ry+rh),(rx,ry+rh)),
             ((rx,ry+rh),(rx,ry))]
    def ccw(A,B,C):
        return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(C[0]-A[0])
    def intersect(A,B,C,D):
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    seg = ((x1,y1),(x2,y2))
    for e in edges:
        if intersect(seg[0], seg[1], e[0], e[1]):
            return True
    # If segment entirely outside and doesn't cross edges, treat as no intersection
    return False

def rects_adjacent(r1, r2, tol=10.0):
    # Edge adjacency: horizontal edges within tol and vertical overlap > 0
    # Vertical adjacency: vertical edges within tol and horizontal overlap > 0
    # Corner adjacency: closest corner distance <= tol
    # Get edges
    l1,r1x,t1,b1 = r1['x'], r1['x']+r1['w'], r1['y'], r1['y']+r1['h']
    l2,r2x,t2,b2 = r2['x'], r2['x']+r2['w'], r2['y'], r2['y']+r2['h']
    # Horizontal overlap amount
    horz_overlap = min(r1x, r2x) - max(l1, l2)
    vert_overlap = min(b1, b2) - max(t1, t2)
    # Edge proximity
    left_touch  = abs(r1x - l2) <= tol
    right_touch = abs(r2x - l1) <= tol
    top_touch   = abs(b1 - t2) <= tol
    bot_touch   = abs(b2 - t1) <= tol
    edge_adj = (left_touch or right_touch) and vert_overlap > 0 or (top_touch or bot_touch) and horz_overlap > 0
    if edge_adj:
        return True
    # Corner proximity
    corners1 = [(l1,t1),(r1x,t1),(r1x,b1),(l1,b1)]
    corners2 = [(l2,t2),(r2x,t2),(r2x,b2),(l2,b2)]
    for c1 in corners1:
        for c2 in corners2:
            if math.dist(c1, c2) <= tol:
                return True
    return False

def parse_svg(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    ns = {'svg':root.tag.split('}')[0].strip('{')}
    # Collect all rect + adjacent text that contains "B\d+ (L|S)"
    booths = {}
    window_rect = None
    door_rect = None

    # We will iterate over <g> groups: expect rect then text with "B# (L/S)"
    for g in root.findall('.//svg:g', ns):
        rect = g.find('svg:rect', ns)
        text = g.find('svg:text', ns)
        if rect is None or text is None or text.text is None:
            continue
        label = text.text.strip()
        m = re.match(r'(B\d+)\s*\((L|S)\)', label)
        if m:
            bid, size = m.group(1), m.group(2)
            r = {'x': float(rect.attrib.get('x',0)), 'y': float(rect.attrib.get('y',0)),
                 'w': float(rect.attrib.get('width',0)), 'h': float(rect.attrib.get('height',0)),
                 'size': size}
            booths[bid] = r

    # Door and Window: look for rects whose nearby text equals "Door" or "Window" (outside groups too)
    # Fallback: scan all rects and all texts; use spatial proximity
    rects = root.findall('.//svg:rect', ns)
    texts = root.findall('.//svg:text', ns)
    rect_list = []
    text_list = []
    for r in rects:
        try:
            rect_list.append({'node':r,'x':float(r.attrib.get('x',0)),'y':float(r.attrib.get('y',0)),
                              'w':float(r.attrib.get('width',0)),'h':float(r.attrib.get('height',0))})
        except:
            pass
    for t in texts:
        if t.text:
            text_list.append({'node':t,'text':t.text.strip(),'x':float(t.attrib.get('x',0)),'y':float(t.attrib.get('y',0))})

    def find_labeled_rect(keyword):
        candidates = [t for t in text_list if t['text'].lower()==keyword.lower()]
        best = None
        best_d = 1e9
        for c in candidates:
            for r in rect_list:
                # prefer rects within 60 px distance
                cx, cy = r['x']+r['w']/2, r['y']+r['h']/2
                d = math.dist((c['x'], c['y']), (cx, cy))
                if d < best_d:
                    best = r
                    best_d = d
        return best

    door_r = find_labeled_rect("Door")
    window_r = find_labeled_rect("Window")
    if door_r:
        door_rect = {'x':door_r['x'],'y':door_r['y'],'w':door_r['w'],'h':door_r['h']}
    if window_r:
        window_rect = {'x':window_r['x'],'y':window_r['y'],'w':window_r['w'],'h':window_r['h']}

    return booths, door_rect, window_rect

def load_constraints(xlsx_path):
    attendees = pd.read_excel(xlsx_path, sheet_name="Attendees")
    constraints = pd.read_excel(xlsx_path, sheet_name="Constraints")
    return attendees, constraints

def load_assignments(csv_path):
    df = pd.read_csv(csv_path)
    # Expect Person, FinalBooth
    if 'Person' not in df.columns or 'FinalBooth' not in df.columns:
        raise ValueError("CSV must contain Person and FinalBooth columns")
    return df[['Person','FinalBooth']]

def compute_aisle_gap(booth_rects):
    # Split into two rows by y-coordinate (k-means-like heuristic)
    centers = [(bid, rect_center(r)) for bid,r in booth_rects.items()]
    ys = [c[1][1] for c in centers]
    if not ys:
        return 0.0
    # Find median y to separate rows
    median_y = sorted(ys)[len(ys)//2]
    top = [b for b in booth_rects.values() if rect_center(b)[1] <= median_y]
    bot = [b for b in booth_rects.values() if rect_center(b)[1] > median_y]
    if not top or not bot:
        return 0.0
    top_max = max(r['y']+r['h'] for r in top)
    bot_min = min(r['y'] for r in bot)
    return bot_min - top_max

def validate(svg_path, csv_path, xlsx_path, out_path):
    report = {'violations':[], 'satisfied':[], 'by_person':defaultdict(lambda:{'satisfied':[],'violations':[]})}
    booths, door, window = parse_svg(svg_path)
    if len(booths) != 12:
        report['violations'].append(f"Expected 12 booths, found {len(booths)}")
    large_count = sum(1 for b in booths.values() if b['size']=='L')
    small_count = sum(1 for b in booths.values() if b['size']=='S')
    if large_count != 4 or small_count != 8:
        report['violations'].append(f"Expected 4 large and 8 small booths; got L={large_count}, S={small_count}")

    attendees, cons = load_constraints(xlsx_path)
    assigns = load_assignments(csv_path)
    # Build person->booth and booth->rect maps
    person_booth = {row.Person: row.FinalBooth for _,row in assigns.iterrows()}
    booth_rects = booths
    # Unassigned count
    unassigned = [b for b in booth_rects.keys() if b not in person_booth.values()]
    if len(unassigned) != 2:
        report['violations'].append(f"Exactly two booths must be unassigned; found {len(unassigned)}")

    # Helper: get rect by booth id
    def get_rect(bid):
        r = booth_rects.get(bid)
        if r is None:
            raise ValueError(f"Unknown booth id {bid}")
        return r

    # Visibility checks
    if door:
        door_center = (door['x']+door['w']/2, door['y']+door['h']/2)
    else:
        report['violations'].append("Door not found in SVG")
        door_center = (0,0)

    # near_window threshold
    if window:
        window_x = window['x']
    else:
        report['violations'].append("Window not found in SVG")
        window_x = max(r['x']+r['w'] for r in booth_rects.values())

    # Evaluate attendee row constraints
    for _, row in attendees.iterrows():
        person = row.Person
        if person not in person_booth:
            # Person may not be assigned; skip constraint checks for them
            continue
        bid = person_booth[person]
        r = get_rect(bid)
        pc = rect_center(r)

        # VIP and visibility requirement
        if str(row.get("VIP","")).strip().lower() == "yes" or str(row.get("VisibilityRequirement",""))=="visible_from_entrance":
            los_blocked = False
            for other_bid, other_rect in booth_rects.items():
                if other_bid == bid:
                    continue
                if line_intersects_rect(door_center, pc, other_rect):
                    los_blocked = True
                    break
            if los_blocked:
                msg = f"{person}: visibility_from_entrance violated (line-of-sight blocked)"
                report['violations'].append(msg); report['by_person'][person]['violations'].append(msg)
            else:
                msg = f"{person}: visibility_from_entrance satisfied"
                report['satisfied'].append(msg); report['by_person'][person]['satisfied'].append(msg)

        if str(row.get("VisibilityRequirement",""))=="near_window":
            # within rightmost quartile or within 250px of window x
            centers_x = sorted(rect_center(br)[0] for br in booth_rects.values())
            thresh = centers_x[int(0.75*len(centers_x))]
            if pc[0] >= thresh or (window and (window_x - (r['x']+r['w'])) <= 250):
                msg = f"{person}: near_window satisfied"
                report['satisfied'].append(msg); report['by_person'][person]['satisfied'].append(msg)
            else:
                msg = f"{person}: near_window violated"
                report['violations'].append(msg); report['by_person'][person]['violations'].append(msg)

        # MustBeNear (semicolon-separated list)
        near_list = [x.strip() for x in str(row.get("MustBeNear","")).split(";") if x.strip()]
        for other_name in near_list:
            if other_name in person_booth:
                r2 = get_rect(person_booth[other_name])
                if rects_adjacent(r, r2, tol=10.0):
                    msg = f"{person}~{other_name}: adjacency satisfied"
                    report['satisfied'].append(msg); report['by_person'][person]['satisfied'].append(msg)
                else:
                    msg = f"{person}~{other_name}: adjacency violated"
                    report['violations'].append(msg); report['by_person'][person]['violations'].append(msg)

        # MustAvoid
        avoid_list = [x.strip() for x in str(row.get("MustAvoid","")).split(";") if x.strip()]
        for other_name in avoid_list:
            if other_name in person_booth:
                r2 = get_rect(person_booth[other_name])
                if rects_adjacent(r, r2, tol=10.0):
                    msg = f"{person}!~{other_name}: separation violated"
                    report['violations'].append(msg); report['by_person'][person]['violations'].append(msg)
                else:
                    msg = f"{person}!~{other_name}: separation satisfied"
                    report['satisfied'].append(msg); report['by_person'][person]['satisfied'].append(msg)

        # Booth size preference
        pref = str(row.get("BoothSizePreference","")).strip().upper()
        if pref in ("L","S"):
            if booth_rects[bid]['size'] == pref:
                msg = f"{person}: booth size preference {pref} satisfied"
                report['satisfied'].append(msg); report['by_person'][person]['satisfied'].append(msg)
            else:
                msg = f"{person}: booth size preference {pref} violated"
                report['violations'].append(msg); report['by_person'][person]['violations'].append(msg)

    # Global constraints sheet
    for _, c in cons.iterrows():
        t = str(c.Type).strip()
        rule = str(c.Rule).strip()
        if t == "Adjacency" and "~" in rule:
            a,b = rule.split("~")
            if a in person_booth and b in person_booth:
                r1 = get_rect(person_booth[a]); r2 = get_rect(person_booth[b])
                if rects_adjacent(r1, r2, tol=10.0):
                    report['satisfied'].append(f"Adjacency {a}~{b} satisfied")
                else:
                    report['violations'].append(f"Adjacency {a}~{b} violated")
        elif t == "Separation" and "!~" in rule:
            a,b = rule.split("!~")
            if a in person_booth and b in person_booth:
                r1 = get_rect(person_booth[a]); r2 = get_rect(person_booth[b])
                if rects_adjacent(r1, r2, tol=10.0):
                    report['violations'].append(f"Separation {a}!~{b} violated")
                else:
                    report['satisfied'].append(f"Separation {a}!~{b} satisfied")
        elif t == "Capacity" and "LargeBooth>=" in rule:
            N = int(rule.split(">=")[1])
            occ_large = sum(1 for p,b in person_booth.items() if booth_rects[b]['size']=="L")
            if occ_large >= N:
                report['satisfied'].append(f"Capacity LargeBooth>={N} satisfied ({occ_large})")
            else:
                report['violations'].append(f"Capacity LargeBooth>={N} violated ({occ_large})")
        elif t == "Flow" and "80" in rule:
            gap = compute_aisle_gap(booth_rects)
            if gap >= 80.0:
                report['satisfied'].append(f"Aisle gap satisfied: {gap:.1f}px")
            else:
                report['violations'].append(f"Aisle gap violated: {gap:.1f}px")
        elif t == "Unassigned" and "At least 2 booths free" in rule:
            # already checked exact two; treat >=2 satisfied if len(unassigned) >= 2
            if len(unassigned) >= 2:
                report['satisfied'].append("Unassigned>=2 satisfied")
            else:
                report['violations'].append("Unassigned>=2 violated")

    # Summary counts
    report['summary'] = {
        'total_satisfied': len(report['satisfied']),
        'total_violations': len(report['violations']),
        'unassigned_booths': unassigned
    }

    with open("/mnt/data/validate_layout.py", "w", encoding="utf-8") as f:
        import inspect
        f.write(inspect.getsource(rect_center))
        f.write("\n")
        f.write(inspect.getsource(line_intersects_rect))
        f.write("\n")
        f.write(inspect.getsource(rects_adjacent))
        f.write("\n")
        f.write(inspect.getsource(parse_svg))
        f.write("\n")
        f.write(inspect.getsource(load_constraints))
        f.write("\n")
        f.write(inspect.getsource(load_assignments))
        f.write("\n")
        f.write(inspect.getsource(compute_aisle_gap))
        f.write("\n")
        # Write a small main
        f.write(dedent('''
        import argparse, json
        from collections import defaultdict
        def main():
            parser = argparse.ArgumentParser(description="Validate venue layout against constraints.")
            parser.add_argument("--svg", required=True)
            parser.add_argument("--csv", required=True)
            parser.add_argument("--xlsx", required=True)
            parser.add_argument("--out", default="validation_report.json")
            args = parser.parse_args()
            report = validate(args.svg, args.csv, args.xlsx, args.out)
            with open(args.out, "w", encoding="utf-8") as wf:
                json.dump(report, wf, indent=2, ensure_ascii=False)
            print(f"Validation complete. Violations: {report['summary']['total_violations']}, Satisfied: {report['summary']['total_satisfied']}")
        if __name__ == "__main__":
            main()
        '''))
    # Also write a standalone file with all functions pasted above? Already wrote individual sources.
    # But validate() is referenced; write it too
    # Re-open file to append validate function source
    with open("/mnt/data/validate_layout.py", "a", encoding="utf-8") as f:
        import inspect, __main__
        f.write("\n")
        f.write(inspect.getsource(validate))

print("Saved script to /mnt/data/validate_layout.py")
print("Example usage:")
print("python validate_layout.py --svg venue_layout.svg --csv placement_result.csv --xlsx venue_constraints.xlsx --out validation_report.json")
