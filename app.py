"""
ReLoop — keep it in the loop
A pure-Python Streamlit app. No JavaScript, Java or C++.

Run locally:   pip install streamlit  &&  streamlit run app.py
Host free:     push to GitHub, then deploy on https://share.streamlit.io
"""

import streamlit as st

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(page_title="ReLoop — keep it in the loop",
                   page_icon="🌱", layout="wide")

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------
LANES = {
    "reuse": {
        "label": "Reuse",
        "accent": "#169d57",
        "cats": [
            ("clothes",   "👕", "Clothes & footwear", "Lots & bundles", "Outgrown lots, age-banded — for families, resellers & NGOs."),
            ("toys",      "🧸", "Toys & games",       "Bulk buyers",    "Bundles for daycares, NGOs & event hosts."),
            ("furniture", "🪑", "Furniture",          "Single or lots", "Usable or restore-able — for homes & refurbishers."),
            ("books",     "📚", "Books & stationery", "Lots",           "Bundles for schools, libraries & NGOs."),
            ("kitchen",   "🍽️", "Kitchen & household","Reuse",          "Utensils, jars, containers still going strong."),
            ("tools",     "🛠️", "Tools & hardware",   "Reuse",          "For makers, repairers & small workshops."),
        ],
    },
    "recycle": {
        "label": "Recycle",
        "accent": "#0d9488",
        "cats": [
            ("plastic", "🧴", "Plastic",           "By weight", "Bottles, containers, packaging, broken plastic & toys."),
            ("paper",   "📦", "Paper & cardboard", "By weight", "Cartons, newspaper, office paper — clean & dry."),
            ("metal",   "🥫", "Metal",             "By weight", "Cans, scrap steel, spent utensils — pays best per kg."),
            ("glass",   "🫙", "Glass",             "By weight", "Bottles & jars, sorted by colour for cullet."),
            ("textile", "🧵", "Textile scrap",     "By weight", "Worn-out clothes & off-cuts → shredded for fibre."),
            ("wood",    "🪵", "Wood",              "By weight", "Off-cuts, pallets & broken furniture wood."),
        ],
    },
}

# Reuse seed:   (title, meta, price, buyer)
# Recycle seed: (title, meta, rate, weight)
SEED = {
    "clothes": [("Toddler clothes lot — 25 pcs", "Ages 2–4 · good condition", "₹450 / lot", "Families & resellers"),
                ("School uniforms ×12", "Lightly used", "₹600 / lot", "Schools & NGOs"),
                ("Footwear bundle ×8", "Sizes 3–6", "₹500 / lot", None)],
    "toys":    [("Mixed toy bundle — 30 pcs", "Cleaned & sorted", "₹700 / lot", "Daycares & NGOs"),
                ("Board games ×6", "Complete sets", "₹500 / lot", "Event hosts"),
                ("Soft toys ×15", "Washed", "₹400 / lot", "NGOs")],
    "furniture":[("Study chairs ×4", "Sturdy, minor wear", "₹1200 / lot", "Refurbishers"),
                ("Office desk", "Good condition", "₹1500", None)],
    "books":   [("Story books ×40", "Grades 3–6", "₹600 / lot", "Schools & libraries"),
                ("Engg textbooks ×10", "1st year", "₹500 / lot", "Students")],
    "kitchen": [("Steel utensil set", "Fully usable", "₹350", None),
                ("Glass jars ×10", "With lids", "₹250 / lot", None)],
    "tools":   [("Hand tools lot", "Hammer, pliers, etc", "₹600 / lot", "Makers & repairers"),
                ("Brushes & rollers ×8", "Cleaned", "₹200 / lot", None)],
    "plastic": [("Sorted PET bottles", "Clean, label-free", "₹18 / kg", "25 kg available"),
                ("HDPE containers", "Rinsed", "₹22 / kg", "15 kg available"),
                ("Mixed rigid plastic", "Incl. broken toys", "₹12 / kg", "40 kg available")],
    "paper":   [("Cardboard — flattened", "Dry & clean", "₹9 / kg", "60 kg available"),
                ("Old newspapers", "Bundled", "₹12 / kg", "30 kg available"),
                ("Office paper", "Mixed", "₹10 / kg", "20 kg available")],
    "metal":   [("Aluminium cans", "Crushed", "₹95 / kg", "8 kg available"),
                ("Scrap steel utensils", "Beyond use", "₹35 / kg", "18 kg available")],
    "glass":   [("Glass bottles", "Sorted by colour", "₹3 / kg", "50 kg available"),
                ("Jar cullet", "Clean", "₹4 / kg", "30 kg available")],
    "textile": [("Worn cotton clothing", "For shredding", "₹8 / kg", "22 kg available"),
                ("Fabric off-cuts", "Mixed", "₹10 / kg", "15 kg available")],
    "wood":    [("Plywood off-cuts", "Project-sized", "₹6 / kg", "35 kg available"),
                ("Broken furniture wood", "Salvageable", "₹5 / kg", "28 kg available")],
}

EMOJI = {cid: e for lane in LANES.values() for (cid, e, *_rest) in lane["cats"]}

# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
def init_state():
    d = st.session_state
    d.setdefault("page", "auth")
    d.setdefault("user", {})
    d.setdefault("health", 0.18)
    d.setdefault("loops", 0)
    d.setdefault("kg", 0.0)
    d.setdefault("action", "shop")
    d.setdefault("lane", "reuse")
    d.setdefault("category", None)
    d.setdefault("posted", {})       # category -> list of dicts
    d.setdefault("rescued", set())   # remembers which seed items were taken

init_state()

def go(page):
    st.session_state.page = page

def state_word(h):
    return "Choking" if h < 0.33 else ("Recovering" if h < 0.7 else "Thriving")

def reward(points, kg):
    st.session_state.health = min(1.0, st.session_state.health + points / 100)
    st.session_state.loops += 1
    st.session_state.kg += kg

def lerp(c1, c2, t):
    """blend two hex colours by t in 0..1 -> hex string"""
    a = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    m = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % m

# ----------------------------------------------------------------------
# Styling (CSS only — no scripts)
# ----------------------------------------------------------------------
st.markdown("""
<style>
.block-container{max-width:1080px;padding-top:1.2rem}
h1,h2,h3{font-family:Georgia,serif;letter-spacing:-.01em}
.rl-card{background:#fff;border:1px solid #e7e7e0;border-radius:16px;padding:18px 18px 14px;
         box-shadow:0 14px 34px -22px rgba(20,30,25,.5);height:100%}
.rl-tile{height:120px;border-radius:12px;display:flex;align-items:center;justify-content:center;
         font-size:54px;margin-bottom:10px;filter:drop-shadow(0 5px 9px rgba(0,0,0,.12))}
.rl-tag{display:inline-block;font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;
        background:#eef3ea;color:#0f7d44;margin-bottom:6px}
.rl-tag.recycle{color:#0a6e64;background:#e6f3f1}
.rl-name{font-family:Georgia,serif;font-weight:600;font-size:17px;margin:2px 0}
.rl-sub{font-size:12.5px;color:#5d6b63;line-height:1.35}
.rl-price{font-family:Georgia,serif;font-weight:700;font-size:18px;margin-top:4px}
.rl-buyer{display:inline-block;font-size:11px;font-weight:600;color:#0f7d44;background:#eef3ea;
          padding:3px 8px;border-radius:999px;margin-top:4px}
.rl-meta{font-size:12px;color:#7a857d}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Sidebar: brand + living planet meter
# ----------------------------------------------------------------------
def sidebar():
    h = st.session_state.health
    sky  = lerp("#6b6253", "#7ec8f2", h)
    land = lerp("#7a6f54", "#5fae54", h)
    leaf_op = round(h, 2)
    trash_op = round(1 - h, 2)
    svg = f"""
    <svg viewBox="0 0 300 180" width="100%" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="300" height="180" fill="{sky}"/>
      <circle cx="245" cy="40" r="20" fill="#ffe7a3" opacity="{leaf_op}"/>
      <path d="M0 130 Q75 115 150 130 T300 130 V180 H0 Z" fill="{land}"/>
      <rect x="143" y="95" width="9" height="45" rx="3" fill="#4a3b2a" opacity="{round(0.4+trash_op*0.6,2)}"/>
      <circle cx="147" cy="92" r="22" fill="#3f9e4a" opacity="{leaf_op}"/>
      <circle cx="128" cy="100" r="15" fill="#3f9e4a" opacity="{leaf_op}"/>
      <circle cx="166" cy="102" r="16" fill="#3f9e4a" opacity="{leaf_op}"/>
      <rect x="40" y="150" width="16" height="10" rx="2" fill="#9a8d6b" opacity="{trash_op}"/>
      <circle cx="250" cy="158" r="6" fill="#8d8068" opacity="{trash_op}"/>
    </svg>"""
    st.sidebar.markdown("### 🌱 ReLoop")
    st.sidebar.caption("Keep it in the loop")
    if st.session_state.user:
        st.sidebar.markdown(svg, unsafe_allow_html=True)
        st.sidebar.progress(h, text=f"Planet: **{state_word(h)}**")
        c1, c2 = st.sidebar.columns(2)
        c1.metric("Items looped", st.session_state.loops)
        c2.metric("Kept from landfill", f"{st.session_state.kg:.1f} kg")
        st.sidebar.divider()
        if st.sidebar.button("🏠 Home", use_container_width=True):
            go("hub"); st.rerun()
        if st.sidebar.button("Log out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
def page_auth():
    st.title("ReLoop")
    st.caption("KEEP IT IN THE LOOP")
    st.write("Reused while it's usable, remade into material when it's spent.")
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])
    with tab_login:
        email = st.text_input("Email", key="li_email")
        st.text_input("Password", type="password", key="li_pass")
        if st.button("Log in", type="primary", use_container_width=True):
            if email.strip():
                st.session_state.user = {"name": email.split("@")[0].replace(".", " ").replace("_", " ")}
                go("hub"); st.rerun()
            else:
                st.warning("Enter your email to continue.")
    with tab_signup:
        email = st.text_input("Email", key="su_email")
        pw = st.text_input("Create a password", type="password", key="su_pass")
        if st.button("Continue", type="primary", use_container_width=True):
            if not email.strip():
                st.warning("Enter your email to continue.")
            elif len(pw) < 6:
                st.warning("Password needs at least 6 characters.")
            else:
                st.session_state.user = {"email": email}
                go("profile"); st.rerun()

def page_profile():
    st.title("Tell us who you are")
    st.write("This helps match you with the right items, materials and buyers.")
    name = st.text_input("Full name")
    prof = st.selectbox("You are a…",
        ["Select one…", "Household", "Maker / Student", "Daycare / School / NGO",
         "Small business / Workshop", "Recycler / Scrap dealer", "Refurbisher / Reseller", "Other"])
    city = st.text_input("City", placeholder="e.g. Hyderabad")
    if st.button("Enter ReLoop", type="primary"):
        if not name.strip():
            st.warning("Add your name to continue.")
        elif prof == "Select one…":
            st.warning("Pick what you are to continue.")
        else:
            st.session_state.user = {"name": name, "prof": prof, "city": city}
            go("hub"); st.rerun()

def page_hub():
    first = st.session_state.user.get("name", "there").split(" ")[0].title()
    st.title(f"Hi {first}")
    st.write("Keep things in the loop — reused while usable, remade when spent. What would you like to do?")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🔍 Rescue an item")
        st.caption("Browse reusable goods and recyclable materials others no longer need — and keep them looping.")
        if st.button("Rescue an item", use_container_width=True, type="primary"):
            st.session_state.action = "shop"; go("lane"); st.rerun()
    with c2:
        st.markdown("#### 📦 Pass it on")
        st.caption("List something you're done with — as a usable item or as material — so it reaches its next loop.")
        if st.button("Pass it on", use_container_width=True):
            st.session_state.action = "post"; go("lane"); st.rerun()

def page_lane():
    act = st.session_state.action
    st.title("What are you looking for?" if act == "shop" else "What are you passing on?")
    st.caption("Still usable as-is, or only good for material? Pick the lane.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<span class="rl-tag">Still usable as-is</span>', unsafe_allow_html=True)
        st.markdown("### ♻️ Reuse")
        st.write("Whole items that still do their job — sold with a price and condition, often in lots for bulk buyers.")
        st.caption("Sold per item / per lot · ₹ price")
        if st.button("Enter Reuse lane", use_container_width=True, type="primary"):
            st.session_state.lane = "reuse"; go("category"); st.rerun()
    with c2:
        st.markdown('<span class="rl-tag recycle">Spent — only good for material</span>', unsafe_allow_html=True)
        st.markdown("### 🔁 Recycle")
        st.write("Material to be remade — bought by weight in bulk by recyclers and makers. The part most marketplaces ignore.")
        st.caption("Sold by weight · ₹ / kg")
        if st.button("Enter Recycle lane", use_container_width=True):
            st.session_state.lane = "recycle"; go("category"); st.rerun()
    st.divider()
    if st.button("← Home"):
        go("hub"); st.rerun()

def tile_html(emoji, g1, g2):
    bg = f"radial-gradient(120% 90% at 30% 20%, {lerp('#ffffff', g1, 0.35)}, {g2})"
    return f'<div class="rl-tile" style="background:{bg}">{emoji}</div>'

GRAD = {  # soft per-category gradients
    "clothes": ("#ffd9e0", "#f0a8b8"), "toys": ("#fff0c2", "#f2cf86"),
    "furniture": ("#e7d3b3", "#caa877"), "books": ("#cfe3ff", "#9ec2f0"),
    "kitchen": ("#d6efe2", "#a3d6c0"), "tools": ("#e3dcc9", "#c3b58e"),
    "plastic": ("#cfe8ff", "#9ec9f0"), "paper": ("#ead9c3", "#d3b88f"),
    "metal": ("#dfe3e8", "#b3bcc6"), "glass": ("#cdeede", "#9fd3bd"),
    "textile": ("#ffd9e0", "#eaa6b6"), "wood": ("#e7d3b3", "#caa877"),
}

def page_category():
    lane = st.session_state.lane
    label = LANES[lane]["label"]
    st.title(f"{label} — pick a {'category' if lane=='reuse' else 'material'}")
    st.caption("Whole items, sold with a price & condition." if lane == "reuse"
               else "Material sold by weight (₹/kg) to recyclers & makers.")
    cats = LANES[lane]["cats"]
    for row in range(0, len(cats), 3):
        cols = st.columns(3)
        for col, (cid, emoji, name, tag, sub) in zip(cols, cats[row:row+3]):
            with col:
                g1, g2 = GRAD[cid]
                st.markdown('<div class="rl-card">' + tile_html(emoji, g1, g2) +
                            f'<span class="rl-tag {"recycle" if lane=="recycle" else ""}">{tag}</span>'
                            f'<div class="rl-name">{name}</div><div class="rl-sub">{sub}</div></div>',
                            unsafe_allow_html=True)
                st.write("")
                if st.button(("Browse" if st.session_state.action == "shop" else "List here"),
                             key=f"cat_{cid}", use_container_width=True):
                    st.session_state.category = cid
                    go("list" if st.session_state.action == "shop" else "post"); st.rerun()
    st.divider()
    if st.button("← Back"):
        go("lane"); st.rerun()

def page_list():
    lane = st.session_state.lane
    cid = st.session_state.category
    cat_name = next(c[2] for c in LANES[lane]["cats"] if c[0] == cid)
    st.title(cat_name)
    st.caption("Priced items & lots — reuse as-is." if lane == "reuse"
               else "Sold by weight — material for remaking.")

    mine = st.session_state.posted.get(cid, [])
    if lane == "reuse":
        seeded = [{"t": t, "m": m, "price": p, "buyer": b} for (t, m, p, b) in SEED.get(cid, [])]
    else:
        seeded = [{"t": t, "m": m, "price": p, "weight": w} for (t, m, p, w) in SEED.get(cid, [])]
    items = mine + seeded

    if not items:
        st.info("Nothing here yet — be the first to add something.")
    for row in range(0, len(items), 3):
        cols = st.columns(3)
        for col, it in zip(cols, items[row:row+3]):
            with col:
                g1, g2 = GRAD[cid]
                ribbon = "REUSE" if lane == "reuse" else "BY WEIGHT"
                buyer = f'<div class="rl-buyer">Bought by {it["buyer"]}</div>' if it.get("buyer") else ""
                price = it["price"] if lane == "reuse" else f'{it["price"]} · {it.get("weight","")}'
                st.markdown('<div class="rl-card">' + tile_html(EMOJI[cid], g1, g2) +
                            f'<span class="rl-tag {"recycle" if lane=="recycle" else ""}">{ribbon}</span>'
                            f'<div class="rl-name">{it["t"]}</div>'
                            f'<div class="rl-meta">{it["m"]}</div>{buyer}'
                            f'<div class="rl-price">{price}</div></div>', unsafe_allow_html=True)
                st.write("")
                key = f"take_{cid}_{row}_{it['t']}"
                if key in st.session_state.rescued:
                    st.success("✓ " + ("Rescued" if lane == "reuse" else "Requested"))
                else:
                    if st.button("Rescue" if lane == "reuse" else "Request pickup",
                                 key=key, use_container_width=True, type="primary"):
                        st.session_state.rescued.add(key)
                        if lane == "reuse":
                            reward(6, 0.6)
                        else:
                            reward(8, 3.0)
                        st.rerun()
    st.divider()
    if st.button("← Categories"):
        go("category"); st.rerun()

def page_post():
    lane = st.session_state.lane
    cid = st.session_state.category
    cat_name = next(c[2] for c in LANES[lane]["cats"] if c[0] == cid)
    st.title("List a usable item" if lane == "reuse" else "List material (sold by weight)")
    st.caption(f"{LANES[lane]['label']} · {cat_name}")

    title = st.text_input("Item name" if lane == "reuse" else "Material name")
    if lane == "reuse":
        lot = st.text_input("Lot size / quantity", placeholder="e.g. 25 pieces")
        cond = st.selectbox("Condition", ["Like new", "Good, fully usable", "Worn but works"])
        price = st.text_input("Price (₹)", placeholder="e.g. 450 / lot")
    else:
        weight = st.text_input("Approx. weight available", placeholder="e.g. 25 kg")
        rate = st.text_input("Expected rate (₹ / kg)", placeholder="e.g. 18")
    note = st.text_input("Notes (sorting, who it suits)")

    if st.button("Add to the loop", type="primary"):
        if not title.strip():
            st.warning("Give it a name.")
        else:
            if lane == "reuse":
                meta = " · ".join([x for x in [lot, cond] if x]) or cond
                pr = price if price.startswith("₹") else ("₹" + price if price else "Free")
                item = {"t": title, "m": meta, "price": pr, "buyer": None}
                reward(6, 0.6)
            else:
                pr = ("₹" + rate.strip() + " / kg") if rate.strip() else "Negotiable"
                item = {"t": title, "m": note or "For remaking", "price": pr, "weight": weight}
                reward(8, 3.0)
            st.session_state.posted.setdefault(cid, []).insert(0, item)
            st.success("Listed! It's now in the loop 🌱")
            st.session_state.action = "shop"
            go("list"); st.rerun()

    if lane == "reuse":
        st.divider()
        st.caption("Too worn to reuse? List it as material instead:")
        if st.button("Switch to the Recycle lane →"):
            mapping = {"clothes": "textile", "furniture": "wood", "toys": "plastic",
                       "kitchen": "glass", "books": "paper", "tools": "metal"}
            st.session_state.lane = "recycle"
            st.session_state.category = mapping.get(cid, "plastic")
            go("post"); st.rerun()

    st.divider()
    if st.button("← Categories"):
        go("category"); st.rerun()

# ----------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------
sidebar()
page = st.session_state.page
{
    "auth": page_auth, "profile": page_profile, "hub": page_hub,
    "lane": page_lane, "category": page_category, "list": page_list, "post": page_post,
}.get(page, page_auth)()