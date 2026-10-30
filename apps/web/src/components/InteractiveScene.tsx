"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import { useRouter } from "next/navigation";

interface Hotspot {
  key: number;
  name: string;
  section: string;
  path: string;
  desc: string;
  status: "ok" | "soon";
  statusText: string;
  position: [number, number, number];
  radius: number;
  group: THREE.Group | null;
  sc?: number;
}

/**
 * InteractiveScene — інтерактивна 3D-сценка «Площа Конституції, Київ»
 * на базі Three.js. Клік по об'єкті відкриває відповідний розділ сайту.
 */
export default function InteractiveScene({
  className = "",
  height = "420px",
}: {
  className?: string;
  height?: string;
} = {}) {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number | null>(null);

  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const rootRef = useRef<THREE.Group | null>(null);

  // Interactive objects (meshes with userData.key -> hotspot index)
  const hotspotMeshesRef = useRef<THREE.Mesh[]>([]);

  // Animation state
  const stateRef = useRef({
    dayT: 1,
    day: 1,
    doorF: 0,
    idle: 0,
    sel: -1,
    hov: -1,
    drag: null as { x: number; y: number; mv: number } | null,
    cur: { y: 0.8, p: 0.58, r: 19, t: new THREE.Vector3(0, 0.8, 0) } as { y: number; p: number; r: number; t: THREE.Vector3 },
    goal: { y: 0.8, p: 0.58, r: 17, t: new THREE.Vector3(0, 0.8, 0) } as { y: number; p: number; r: number; t: THREE.Vector3 },
  });

  const [cardOpen, setCardOpen] = useState(false);
  const [cardData, setCardData] = useState<{
    name: string;
    section: string;
    desc: string;
    status: string;
    statusText: string;
    path: string;
  } | null>(null);
  const [isNight, setIsNight] = useState(false);

  const hotspots: Hotspot[] = [
    {
      key: 0,
      name: "Верховна Рада",
      section: "Розділ «Пошук законодавства»",
      path: "/uk/legislation",
      desc: "Шукайте акти за назвою, статтею чи змістом і дивіться, яким закон був на будь-яку дату.",
      status: "ok",
      statusText: "підключено",
      position: [0.8, 1.3, -2.5],
      radius: 9,
      group: null,
    },
    {
      key: 1,
      name: "Терези",
      section: "Розділ «Протиріччя та колізії»",
      path: "/uk/conflicts",
      desc: "Хто кого перебиває: вища сила, спеціальна норма, новіша норма. Кожне рішення з поясненням правила.",
      status: "soon",
      statusText: "скоро",
      position: [3.2, 1.4, 1.5],
      radius: 6,
      group: null,
    },
    {
      key: 2,
      name: "Поштова скринька",
      section: "Розділ «Моніторинг»",
      path: "/uk/monitoring",
      desc: "Підпишіться на акт чи тему й отримуйте дайджест змін на пошту або в Telegram.",
      status: "soon",
      statusText: "скоро",
      position: [-3.35, 0.9, 2.85],
      radius: 5.5,
      group: null,
    },
    {
      key: 3,
      name: "Стос книг",
      section: "Розділи «Мої документи» та «Аналіз договорів»",
      path: "/uk/contracts",
      desc: "Закладки, нотатки й розбір договорів по пунктах із посиланнями на статті.",
      status: "soon",
      statusText: "скоро",
      position: [-1, 0.3, 2.7],
      radius: 5,
      group: null,
    },
    {
      key: 4,
      name: "Річка та міст",
      section: "Розділ «Карта законодавства»",
      path: "/uk/legal-map",
      desc: "Міст між берегами показує, як акти пов'язані: хто кого змінює, скасовує чи на кого посилається.",
      status: "soon",
      statusText: "скоро",
      position: [2.6, 0.4, 4.45],
      radius: 7,
      group: null,
    },
    {
      key: 5,
      name: "Золоті куполи",
      section: "Розділ «AI Юрист-дослідник»",
      path: "/uk/assistant",
      desc: "Помічник, який відповідає лише з посиланням на статті. Якщо норми в базі немає, так і скаже.",
      status: "soon",
      statusText: "скоро",
      position: [4.9, 1, 2.3],
      radius: 6.5,
      group: null,
    },
    {
      key: 6,
      name: "Вулиця",
      section: "Розділ «Нові закони та зміни»",
      path: "/uk/changes",
      desc: "Безперервний потік змін: що змінилось останнім часом, кого це стосується і що робити.",
      status: "soon",
      statusText: "скоро",
      position: [-4.9, 0.2, 1],
      radius: 8,
      group: null,
    },
  ];

  const pick = useCallback(
    (x: number, y: number) => {
      const camera = cameraRef.current;
      const scene = sceneRef.current;
      const canvas = canvasRef.current;
      if (!camera || !scene || !canvas) return -1;
      const rect = canvas.getBoundingClientRect();
      const ms = new THREE.Vector2(
        (x / rect.width) * 2 - 1,
        -(y / rect.height) * 2 + 1,
      );
      const ray = new THREE.Raycaster();
      ray.setFromCamera(ms, camera);
      const hits = ray.intersectObjects(hotspotMeshesRef.current);
      return hits.length ? (hits[0].object.userData.key as number) : -1;
    },
    [],
  );

  const selectHotspot = useCallback(
    (k: number) => {
      const h = hotspots[k];
      if (!h) return;
      stateRef.current.sel = k;
      const camera = cameraRef.current;
      if (camera) {
        stateRef.current.goal.t.set(h.position[0], h.position[1], h.position[2]);
        stateRef.current.goal.r = h.radius;
        stateRef.current.goal.p = 0.5;
      }
      setCardData({
        name: h.name,
        section: h.section,
        desc: h.desc,
        statusText: h.statusText,
        status: h.status,
        path: h.path,
      });
      setCardOpen(true);
    },
    [],
  );

  const backFromHotspot = useCallback(() => {
    stateRef.current.sel = -1;
    const camera = cameraRef.current;
    if (camera) {
      stateRef.current.goal.t.set(0, 0.8, 0);
      stateRef.current.goal.r = 17;
    }
    setCardOpen(false);
    setCardData(null);
  }, []);

  const toggleDayNight = useCallback(() => {
    setIsNight((prev) => {
      const next = !prev;
      stateRef.current.dayT = next ? 0 : 1;
      return next;
    });
  }, []);

  // CSS styles injected once
  useEffect(() => {
    if (typeof document === "undefined") return;
    const existing = document.getElementById("ai-ugoda-interactive-scene-css");
    if (existing) return;
    const style = document.createElement("style");
    style.id = "ai-ugoda-interactive-scene-css";
    style.textContent = `
      #ai-ugoda-scene-ui {
        position: fixed;
        inset: 0;
        z-index: 20;
        pointer-events: none;
        color: #f3e6bc;
        font-family: Inter, system-ui, sans-serif;
      }
      #ai-ugoda-scene-canvas {
        position: fixed;
        inset: 0;
        z-index: 10;
        display: block;
      }
      .iu-title {
        left: clamp(16px, 3vw, 44px);
        top: clamp(16px, 3vw, 36px);
        max-width: min(430px, 70vw);
      }
      .iu-title h1 {
        font: 600 clamp(26px, 3.6vw, 48px) / 1.08 "Playfair Display", serif;
        color: #f3e6bc;
        margin: 0;
      }
      .iu-title p {
        color: #b3a28a;
        margin-top: 8px;
        font-size: 15px;
        margin: 0;
      }
      .iu-hint {
        left: 50%;
        bottom: calc(14px + env(safe-area-inset-bottom, 0));
        transform: translateX(-50%);
        font-size: 13px;
        color: rgba(179, 162, 138, 0.85);
        white-space: nowrap;
        padding: 8px 16px;
        border-radius: 99px;
        background: rgba(15, 11, 8, 0.55);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        pointer-events: none;
      }
      .iu-card {
        position: fixed;
        right: clamp(12px, 3vw, 40px);
        top: 50%;
        width: min(350px, calc(100% - 24px));
        padding: 22px 24px;
        pointer-events: auto;
        transform: translateY(-50%) translateX(30px);
        opacity: 0;
        visibility: hidden;
        transition: 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        background: linear-gradient(145deg, rgba(74, 46, 28, 0.42), rgba(27, 18, 12, 0.8));
        backdrop-filter: blur(22px) saturate(140%);
        -webkit-backdrop-filter: blur(22px) saturate(140%);
        border: 1px solid rgba(232, 200, 113, 0.28);
        border-radius: 22px;
        box-shadow: inset 0 1px 0 rgba(255, 236, 180, 0.12), 0 30px 70px -24px #000;
        z-index: 30;
      }
      .iu-card.on {
        transform: translateY(-50%);
        opacity: 1;
        visibility: visible;
      }
      .iu-card h2 {
        font: 600 25px / 1.2 "Playfair Display", serif;
        color: #f3e6bc;
        margin: 0 0 2px 0;
      }
      .iu-card .sec {
        color: #e8c871;
        font-size: 14px;
        margin-top: 4px;
      }
      .iu-card p {
        margin-top: 10px;
        font-size: 15.5px;
        line-height: 1.5;
      }
      .iu-badge {
        display: inline-block;
        margin-top: 14px;
        font-size: 13px;
        padding: 3px 12px;
        border-radius: 99px;
        border: 1px solid;
      }
      .iu-badge.ok {
        color: #7fa67a;
        border-color: #7fa67a;
      }
      .iu-badge.soon {
        color: #e0a23b;
        border-color: #e0a23b;
      }
      .iu-row {
        display: flex;
        gap: 8px;
        margin-top: 16px;
        flex-wrap: wrap;
      }
      .iu-btn {
        all: unset;
        cursor: pointer;
        padding: 8px 16px;
        border-radius: 12px;
        border: 1px solid rgba(232, 200, 113, 0.4);
        color: #f3e6bc;
        font-size: 14px;
        transition: 0.2s;
        pointer-events: auto;
      }
      .iu-btn:hover {
        background: rgba(201, 162, 75, 0.2);
      }
      .iu-btn.p {
        background: linear-gradient(135deg, #8f6f2b, #e8c871 50%, #c9a24b);
        color: #1a1006;
        border: 0;
        font-weight: 600;
      }
      .iu-btn:focus-visible {
        outline: 2px solid #e8c871;
        outline-offset: 2px;
      }
      .iu-tip {
        position: fixed;
        z-index: 40;
        pointer-events: none;
        padding: 5px 12px;
        border-radius: 10px;
        font-size: 14px;
        background: rgba(15, 11, 8, 0.8);
        border: 1px solid rgba(232, 200, 113, 0.35);
        color: #f3e6bc;
        opacity: 0;
        transition: opacity 0.2s;
        white-space: nowrap;
      }
      .iu-night-btn {
        position: fixed;
        right: clamp(12px, 3vw, 40px);
        top: clamp(12px, 3vw, 34px);
        z-index: 30;
        pointer-events: auto;
        background: rgba(15, 11, 8, 0.55);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(232, 200, 113, 0.4);
        color: #f3e6bc;
        padding: 8px 16px;
        border-radius: 12px;
        font-size: 14px;
        cursor: pointer;
      }
      .iu-night-btn:hover {
        background: rgba(201, 162, 75, 0.2);
      }
      .iu-err {
        position: fixed;
        inset: 0;
        display: none;
        place-items: center;
        text-align: center;
        padding: 30px;
        color: #b3a28a;
        z-index: 50;
        background: #0c0a0b;
      }
      .iu-vg {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 15;
        background: radial-gradient(ellipse at center, transparent 50%, rgba(4, 2, 1, 0.7) 100%);
      }
      @media (max-width: 700px) {
        .iu-card {
          top: auto;
          bottom: 56px;
          transform: translateY(30px);
        }
        .iu-card.on {
          transform: none;
        }
        .iu-hint {
          display: none;
        }
        .iu-night-btn {
          top: auto;
          bottom: 120px;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        * {
          transition: none !important;
        }
      }
    `;
    document.head.appendChild(style);
    return () => {
      style.remove();
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || typeof document === "undefined") return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const R = new THREE.WebGLRenderer({ canvas, antialias: true });
    R.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 800 ? 1.5 : 2));
    R.setSize(window.innerWidth, window.innerHeight);
    R.shadowMap.enabled = true;
    R.shadowMap.type = THREE.PCFSoftShadowMap;

    const S = new THREE.Scene();
    S.background = new THREE.Color(0x0b0b14);
    S.fog = new THREE.Fog(0x0b0b14, 24, 60);

    const C = new THREE.PerspectiveCamera(32, window.innerWidth / window.innerHeight, 1.5, 90);

    const hemi = new THREE.HemisphereLight(0x6a7aa8, 0x3a2a1c, 0.8);
    S.add(hemi);

    const moon = new THREE.DirectionalLight(0x9db4ff, 0.95);
    moon.position.set(-8, 14, 9);
    moon.castShadow = true;
    moon.shadow.mapSize.set(2048, 2048);
    const sc = moon.shadow.camera;
    sc.left = -10;
    sc.right = 10;
    sc.top = 10;
    sc.bottom = -10;
    sc.near = 1;
    sc.far = 34;
    sc.updateProjectionMatrix();
    moon.shadow.bias = -0.0006;
    moon.shadow.normalBias = 0.03;
    S.add(moon);

    const B = (w: number, h: number, d: number) => new THREE.BoxGeometry(w, h, d);
    const Cy = (a: number, b: number, h: number, s: number) => new THREE.CylinderGeometry(a, b, h, s);
    const Co = (r: number, h: number, s: number) => new THREE.ConeGeometry(r, h, s);

    const MT = new Map<string, THREE.Material>();
    function mat(c: number, o?: Record<string, unknown>) {
      const k = c + JSON.stringify(o || {});
      if (!MT.has(k)) {
        MT.set(k, new THREE.MeshStandardMaterial(Object.assign({ color: c, flatShading: true, roughness: 0.88 }, o || {})));
      }
      return MT.get(k)!;
    }

    function add(g: THREE.Group, geo: THREE.BufferGeometry, c: number, x: number, y: number, z: number, o?: Record<string, unknown>) {
      const m = new THREE.Mesh(geo, mat(c, o));
      m.position.set(x, y, z);
      m.castShadow = true;
      m.receiveShadow = true;
      g.add(m);
      return m;
    }

    const glow: THREE.Material[] = [];
    function win(g: THREE.Group, w: number, h: number, d: number, x: number, y: number, z: number) {
      const m = new THREE.Mesh(B(w, h, d), new THREE.MeshBasicMaterial({ color: 0xffb85a }));
      m.position.set(x, y, z);
      g.add(m);
      glow.push(m.material);
    }

    const dmat = new THREE.MeshStandardMaterial({ color: 0x9a7a2e, roughness: 0.6, emissive: 0xffa850, emissiveIntensity: 0.7, flatShading: true });

    const root = new THREE.Group();
    S.add(root);
    rootRef.current = root;

    const D = new THREE.Object3D();
    const cc = new THREE.Color();
    const c2 = new THREE.Color();
    const rnd = Math.random;

    const fl = (w: number, dd: number, x: number, z: number, c: number, y: number = 0.02, h: number = 0.04) =>
      add(root, B(w, h, dd), c, x, y, z);

    // base plaza + curb
    add(root, B(12, 0.5, 12), 0x77705f, 0, -0.25, 0);
    add(root, B(12.6, 1.3, 12.6), 0x24202c, 0, -0.7, 0);

    // columns around plaza
    for (let s = 0; s < 4; s++) {
      for (let i = 0; i < 9; i++) {
        const u = -5.6 + i * 1.4;
        const p = [[u, 6.36], [u, -6.36], [6.36, u], [-6.36, u]][s];
        const m = new THREE.Mesh(
          B(1.36, 0.78, 0.72),
          new THREE.MeshStandardMaterial({ color: new THREE.Color().setHSL(0.68 + rnd() * 0.03, 0.13, 0.27 + rnd() * 0.1), flatShading: true, roughness: 0.9 }),
        );
        m.position.set(p[0], 0.08, p[1]);
        m.rotation.y = s < 2 ? 0 : 1.5708;
        m.castShadow = true;
        m.receiveShadow = true;
        root.add(m);
      }
    }

    // walls / building masses
    fl(12, 1.2, 0, -5.4, 0x3d6b2f);
    fl(1.9, 8.3, -2.75, -0.85, 0x4a7a38);
    fl(2.2, 8.5, 4.9, -1.1, 0x4a7a38);
    fl(10.2, 0.65, 0.9, 5.68, 0x4a7a38);
    fl(0.5, 8.3, -3.95, -0.85, 0x8d8d8f, 0.025);
    fl(0.4, 12, -5.8, 0, 0x4a7a38);
    fl(2.2, 2.2, 4.9, 2.9, 0x4a7a38);

    // plaza texture
    const GP = document.createElement("canvas");
    GP.width = GP.height = 128;
    {
      const x = GP.getContext("2d")!;
      x.fillStyle = "#b9aea4";
      x.fillRect(0, 0, 128, 128);
      x.strokeStyle = "#8c7f76";
      x.lineWidth = 3;
      x.strokeRect(6, 6, 116, 116);
      x.beginPath();
      x.moveTo(64, 6);
      x.lineTo(122, 64);
      x.lineTo(64, 122);
      x.lineTo(6, 64);
      x.closePath();
      x.stroke();
      x.fillStyle = "#a39689";
      x.fillRect(52, 52, 24, 24);
    }
    const pt = new THREE.CanvasTexture(GP);
    pt.wrapS = pt.wrapT = THREE.RepeatWrapping;
    pt.repeat.set(7, 6);
    const plaza = new THREE.Mesh(B(5.5, 0.04, 4.9), new THREE.MeshStandardMaterial({ map: pt, roughness: 0.9 }));
    plaza.position.set(1.05, 0.02, 0.95);
    plaza.receiveShadow = true;
    root.add(plaza);

    function ground(x: number, z: number) {
      if (x > -0.75 && x < 2.35) {
        if (z < -0.82 && z > -1.62) return 0.02 + ((-0.82 - z) / 0.8) * 0.25;
        if (z <= -1.62 && z > -2.3) return 0.27;
      }
      if (Math.abs(x - 2.6) < 0.45 && z > 3.4 && z < 5.5) {
        const s = (5.5 - z) / 2.1;
        return 0.1 + 0.3 * Math.sin(Math.PI * s);
      }
      return 0.02;
    }

    // river + bridge
    const rv = new THREE.Group();
    rv.position.set(0, 0, 4.45);
    root.add(rv);
    const water = add(rv, B(12, 0.05, 1.8), 0x3d8fb5, 0, 0.025, 0, { roughness: 0.2, metalness: 0.15, emissive: 0x0d3550 });
    add(rv, B(12, 0.22, 0.12), 0x9a9078, 0, 0.11, -0.93);
    add(rv, B(12, 0.22, 0.12), 0x9a9078, 0, 0.11, 0.93);
    const rip: { m: THREE.Mesh; s: number }[] = [];
    for (let i = 0; i < 18; i++) {
      const m = new THREE.Mesh(B(0.55, 0.01, 0.04), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.4 }));
      m.position.set(-6 + rnd() * 12, 0.058, -0.7 + rnd() * 1.4);
      rv.add(m);
      rip.push({ m, s: 0.15 + rnd() * 0.25 });
    }
    for (let i = 0; i <= 8; i++) {
      const s = i / 8;
      const zl = 1.05 - s * 2.1;
      const y = 0.1 + 0.3 * Math.sin(Math.PI * s);
      const m = add(rv, B(0.62, 0.08, 0.28), 0xc9bda0, 2.6, y, zl);
      m.rotation.x = Math.atan((0.3 * Math.PI * Math.cos(Math.PI * s)) / 2.1);
      [-1, 1].forEach((sd) => add(rv, B(0.04, 0.2, 0.04), 0x2a2018, 2.6 + sd * 0.3, y + 0.14, zl));
    }
    [-1.05, 1.05].forEach((zl) => {
      const g = new THREE.Group();
      g.position.set(2.6, 0, zl);
      rv.add(g);
      add(g, Cy(0.03, 0.04, 0.8, 6), 0x2a2018, 0, 0.4, 0);
      win(g, 0.12, 0.16, 0.12, 0, 0.88, 0);
    });

    // street left, car bridge, fence, lampposts
    const rg = new THREE.Group();
    rg.position.set(-4.9, 0, 0);
    root.add(rg);
    add(rg, B(1.4, 0.03, 12), 0x3a3a3e, 0, 0.015, 0);
    for (let z = -5.6; z <= 5.6; z += 0.8) {
      if (z > 3.3 && z < 5.6) continue;
      add(rg, B(0.04, 0.012, 0.35), 0xe8e8e8, 0, 0.036, z);
    }
    add(rg, B(0.03, 0.012, 12), 0xdddddd, -0.62, 0.036, 0);
    add(rg, B(0.03, 0.012, 12), 0xdddddd, 0.62, 0.036, 0);
    add(rg, B(1.5, 0.12, 1.9), 0x4a4a50, 0, 0.1, 4.45);
    [-1, 1].forEach((s) => add(rg, B(0.06, 0.18, 1.9), 0xb8b0a0, s * 0.72, 0.21, 4.45));
    for (let z = -4.8; z <= 3.2; z += 0.27) add(root, B(0.03, 0.28, 0.03), 0x151518, -3.75, 0.16, z);
    add(root, B(0.02, 0.02, 8.1), 0x151518, -3.75, 0.12, -0.8);
    add(root, B(0.02, 0.02, 8.1), 0x151518, -3.75, 0.26, -0.8);
    [-4, -1.6, 0.8, 3].forEach((z) => {
      const g = new THREE.Group();
      g.position.set(-3.95, 0, z);
      root.add(g);
      add(g, Cy(0.03, 0.04, 1.4, 6), 0x1d1d22, 0, 0.7, 0);
      add(g, B(0.4, 0.03, 0.03), 0x1d1d22, -0.18, 1.4, 0);
      win(g, 0.14, 0.06, 0.1, -0.38, 1.37, 0);
    });
    const pl4 = new THREE.Group();
    pl4.position.set(3, 0, 1);
    root.add(pl4);
    add(pl4, Cy(0.04, 0.06, 1.1, 6), 0x1d1d22, 0, 0.55, 0);
    add(pl4, B(0.18, 0.24, 0.18), 0x1d1d22, 0, 1.2, 0);
    win(pl4, 0.12, 0.17, 0.12, 0, 1.2, 0);

    // Verkhovna Rada
    const rd = new THREE.Group();
    rd.position.set(0.8, 0, -3.7);
    root.add(rd);
    const WH = 0xeceeee;
    add(rd, B(5.4, 0.3, 3), 0x6f6f72, 0, 0.15, 0);
    add(rd, B(5.2, 1.5, 2.8), WH, 0, 1.05, 0);
    add(rd, B(5.35, 0.1, 2.95), 0xf6f7f7, 0, 1.85, 0);
    add(rd, B(3, 0.5, 1.2), WH, 0, 2.15, 0.8);
    add(rd, B(3.2, 0.08, 1.3), 0xf6f7f7, 0, 2.44, 0.8);
    add(rd, B(3.1, 0.27, 0.7), 0x8a8a8d, 0, 0.135, 1.75);
    for (let i = 0; i < 6; i++) add(rd, Cy(0.075, 0.085, 1.4, 10), 0xf7f8f8, -1.25 + i * 0.5, 1, 1.85);
    add(rd, B(3.2, 0.18, 0.7), 0xf6f7f7, 0, 1.78, 1.8);
    [-2.3, 2.3].forEach((x) => {
      add(rd, B(1.2, 1.5, 0.3), WH, x, 1.05, 1.55);
      add(rd, B(1.3, 0.08, 0.38), 0xf6f7f7, x, 1.82, 1.55);
    });
    add(rd, Cy(1.1, 1.1, 1.3, 20), WH, -2.9, 0.95, -0.5);
    add(rd, Cy(1.13, 1.13, 0.05, 20), 0x7d8288, -2.9, 1.62, -0.5);
    add(rd, B(1.6, 1.3, 2.4), WH, 3.3, 0.95, -0.1);
    add(rd, B(1.65, 0.05, 2.45), 0x7d8288, 3.3, 1.62, -0.1);
    add(rd, B(5.1, 0.05, 2.7), 0x7d8288, 0, 1.93, 0);
    for (let i = 0; i < 9; i++) add(rd, B(0.14 + rnd() * 0.2, 0.12, 0.14 + rnd() * 0.2), 0x9a9fa5, -2 + rnd() * 4, 2, -1 + rnd() * 1.8);
    const med = add(rd, Cy(0.3, 0.3, 0.05, 24), 0xf2f0e6, 0, 2.15, 1.42);
    med.rotation.x = 1.5708;
    const mr = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.025, 6, 24), mat(0xc9a24b, { metalness: 0.4, emissive: 0x2a1c06 }));
    mr.position.set(0, 2.15, 1.43);
    rd.add(mr);
    add(rd, Cy(1.32, 1.38, 0.1, 24), 0xb08a4a, 0, 1.99, -0.1, { metalness: 0.5 });
    const dgm = new THREE.SphereGeometry(1.25, 16, 8, 0, 6.2832, 0, 1.5708);
    const dm = new THREE.Mesh(dgm, new THREE.MeshStandardMaterial({ color: 0xb9c6cc, transparent: true, opacity: 0.82, roughness: 0.2, metalness: 0.5, emissive: 0x1f3a40, flatShading: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2 }));
    dm.scale.y = 0.55;
    dm.position.set(0, 2.04, -0.1);
    rd.add(dm);
    const de = new THREE.LineSegments(new THREE.EdgesGeometry(dgm), new THREE.LineBasicMaterial({ color: 0xe6edf0 }));
    de.scale.set(1.006, 0.553, 1.006);
    de.position.copy(dm.position);
    rd.add(de);
    add(rd, Cy(0.012, 0.016, 1, 5), 0xc9a24b, 0, 3.22, -0.1);

    function flg(c: number, yy: number) {
      const g = new THREE.PlaneGeometry(0.5, 0.16, 10, 1);
      g.translate(0.25, 0, 0);
      const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: c, side: 2 }));
      m.position.set(0, yy, -0.1);
      m.userData.b = (g.attributes.position as THREE.BufferAttribute).array.slice();
      rd.add(m);
      return m;
    }
    const fT = flg(0x0057b7, 3.6);
    const fB = flg(0xffd700, 3.44);
    [-1, -0.5, 0, 0.5, 1].forEach((x) => {
      const dr = new THREE.Mesh(B(0.26, 0.5, 0.04), dmat);
      dr.position.set(x, 0.55, 1.43);
      rd.add(dr);
    });
    [-2.3, 2.3].forEach((x) => {
      const g = add(rd, B(0.34, 0.34, 0.34), 0x8a8a8d, x * 1.0, 0, 0);
      g.visible = false;
    });
    [
      [-2.4, 2.35],
      [-1.85, 2.45],
      [1.95, 2.45],
      [2.5, 2.35],
    ].forEach((p) => {
      add(rd, B(0.3, 0.26, 0.3), 0x4a4a4e, p[0], 0.13, p[1]);
      add(rd, Cy(0.06, 0.09, 0.32, 5), 0x33433a, p[0] - 0.05, 0.42, p[1]);
      add(rd, new THREE.SphereGeometry(0.06, 6, 5), 0x33433a, p[0] - 0.05, 0.62, p[1]);
      add(rd, Cy(0.05, 0.07, 0.22, 5), 0x33433a, p[0] + 0.08, 0.37, p[1] + 0.04);
    });
    [2.2, 2.4, 2.6, 2.8].forEach((zz, i) => {
      const hh = [0.22, 0.16, 0.1, 0.05][i];
      add(rd, B(3.1, hh, 0.2), 0xa59b86, 0, hh / 2, zz);
    });
    const wl: [number, number, number, number, number, number][] = [];
    [-1, -0.5, 0, 0.5, 1].forEach((x) => wl.push([x, 1.15, 1.43, 0.2, 0.5, 0.04]));
    [-2.55, -2.05, 2.05, 2.55].forEach((x) => [0.65, 1.15].forEach((y) => wl.push([x, y, 1.71, 0.2, 0.4, 0.04])));
    [0, 1].forEach((r) => {
      for (let x = -2.1; x <= 2.11; x += 0.7) {
        if (Math.abs(x) > 1.4) wl.push([x, 0.75 + r * 0.5, 1.41, 0.2, 0.36, 0.04]);
      }
    });
    [-1.5, -0.4, 0.7, 1.8].forEach((z) => [-1, 1].forEach((s) => [0.7, 1.3].forEach((y) => wl.push([s * 2.61, y, z, 0.04, 0.3, 0.2]))));
    const WN = wl.length;
    const WM = new THREE.InstancedMesh(B(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff }), WN);
    const wo: number[] = [];
    wl.forEach((w, i) => {
      D.position.set(w[0], w[1], w[2]);
      D.rotation.set(0, 0, 0);
      D.scale.set(w[3], w[4], w[5]);
      D.updateMatrix();
      WM.setMatrixAt(i, D.matrix);
      wo.push(rnd() < 0.15 ? 0.3 : 1);
      WM.setColorAt(i, cc.setRGB(1, 1, 1));
    });
    WM.frustumCulled = false;
    rd.add(WM);

    // neighbor house
    const nb = new THREE.Group();
    nb.position.set(4.95, 0, -3.2);
    root.add(nb);
    add(nb, B(2.1, 1.7, 4.2), 0xe5d9b3, 0, 0.85, 0);
    add(nb, B(2.25, 0.12, 4.35), 0xf6f1de, 0, 1.76, 0);
    add(nb, B(2, 0.06, 4.1), 0x7d8288, 0, 1.84, 0);
    add(nb, B(2.2, 0.2, 4.3), 0xb9ad86, 0, 0.1, 0);
    const nl: [number, number, number, number, number, number][] = [];
    for (let r = 0; r < 2; r++) {
      for (let z = -1.8; z <= 1.81; z += 0.6) nl.push([-1.06, 0.6 + r * 0.6, z, 0.04, 0.32, 0.2]);
      for (let x = -0.7; x <= 0.71; x += 0.7) nl.push([x, 0.6 + r * 0.6, 2.11, 0.2, 0.32, 0.04]);
    }
    const NN = nl.length;
    const NM = new THREE.InstancedMesh(B(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff }), NN);
    const no: number[] = [];
    nl.forEach((w, i) => {
      D.position.set(w[0], w[1], w[2]);
      D.rotation.set(0, 0, 0);
      D.scale.set(w[3], w[4], w[5]);
      D.updateMatrix();
      NM.setMatrixAt(i, D.matrix);
      no.push(rnd() < 0.3 ? 0.3 : 1);
      NM.setColorAt(i, cc.setRGB(1, 1, 1));
    });
    NM.frustumCulled = false;
    nb.add(NM);

    const pl0 = new THREE.PointLight(0xffa850, 1.3, 8);
    pl0.position.set(0.8, 1.2, -1);
    S.add(pl0);
    const pl1 = new THREE.PointLight(0xffc880, 1, 8);
    pl1.position.set(0.8, 2.6, -3.8);
    S.add(pl1);

    // trees (with NOGO zones to prevent overlapping buildings)
    const TR: { m: THREE.Mesh; p: number }[] = [];
    const NOGO = [[-1.95, 4.95, -5.3, -1.6], [-3.25, -1, -5.35, -3.05], [3.8, 6.1, -5.4, -1], [-1.8, 3.9, -1.6, 3.5], [-5.7, -3.65, -6, 6], [-6, 6, 3.5, 5.35], [3.7, 6.1, 1.2, 3.4]];
    const okT = (x: number, z: number) => !NOGO.some((r) => x > r[0] && x < r[1] && z > r[2] && z < r[3]);
    function tree(x: number, z: number, s: number, k: number) {
      if (!okT(x, z)) return;
      const g = new THREE.Group();
      g.position.set(x, 0, z);
      g.scale.setScalar(s);
      root.add(g);
      if (k) {
        add(g, Cy(0.06, 0.09, 0.4, 5), 0x4a2e1c, 0, 0.2, 0);
        [
          [0.8, 1, 0.7],
          [0.62, 0.9, 1.25],
          [0.42, 0.8, 1.75],
        ].forEach((q, i) => add(g, Co(q[0], q[1], 7), i % 2 ? 0x1f5a30 : 0x276a38, 0, q[2], 0));
      } else {
        add(g, Cy(0.09, 0.13, 0.7, 5), 0x4a2e1c, 0, 0.35, 0);
        const c = [0x3f7a35, 0x4b8a3a, 0x2f6a30, 0x578f3c][Math.floor(rnd() * 4)];
        const cr = add(g, new THREE.IcosahedronGeometry(0.95, 0), c, 0, 1.35, 0);
        cr.scale.y = 0.9 + rnd() * 0.3;
        const c3 = add(g, new THREE.IcosahedronGeometry(0.62, 0), c, 0.35, 1.9, 0.1);
        TR.push({ m: cr, p: rnd() * 6 });
        TR.push({ m: c3, p: rnd() * 6 });
      }
    }
    for (let x = -5.2; x <= 5.3; x += 1.2) tree(x + rnd() * 0.15, -5.75 + rnd() * 0.1, 0.62 + rnd() * 0.12, 0);
    [
      [-2.8, 1.5, 0.95],
      [-2.8, -2.1, 0.95],
      [-1.5, 5.65, 0.45],
      [3.2, 5.65, 0.45],
      [4.6, 5.65, 0.5],
    ].forEach((p) => tree(p[0], p[1], p[2], 0));
    [
      [4.4, -0.6, 0.85],
      [5.2, 0.2, 0.75],
    ].forEach((p) => tree(p[0], p[1], p[2], 1));

    // church
    const chg = new THREE.Group();
    chg.position.set(4.9, 0, 2.3);
    chg.rotation.y = -0.5;
    root.add(chg);
    const ci = new THREE.Group();
    ci.scale.setScalar(0.8);
    chg.add(ci);
    add(ci, B(0.9, 0.8, 0.9), 0xf2eee0, 0, 0.4, 0);
    const rf = add(ci, Co(0.75, 0.35, 4), 0x2b6a5c, 0, 0.98, 0);
    rf.rotation.y = 0.785;
    add(ci, Cy(0.22, 0.24, 0.35, 8), 0xf2eee0, 0, 1.3, 0);
    const od = add(ci, new THREE.SphereGeometry(0.26, 8, 6), 0xc9a24b, 0, 1.62, 0, { metalness: 0.4, emissive: 0x2a1c06 });
    od.scale.y = 1.3;
    add(ci, Co(0.03, 0.25, 4), 0xc9a24b, 0, 2, 0);
    add(ci, B(0.02, 0.2, 0.02), 0xe8c871, 0, 2.2, 0);
    add(ci, B(0.12, 0.02, 0.02), 0xe8c871, 0, 2.24, 0);
    [
      [-0.38, -0.38],
      [0.38, -0.38],
      [-0.38, 0.38],
      [0.38, 0.38],
    ].forEach((q) => {
      add(ci, Cy(0.09, 0.1, 0.25, 6), 0xf2eee0, q[0], 1.08, q[1]);
      const s = add(ci, new THREE.SphereGeometry(0.11, 6, 5), 0xc9a24b, q[0], 1.3, q[1], { metalness: 0.4, emissive: 0x2a1c06 });
      s.scale.y = 1.3;
    });
    add(ci, B(0.3, 1.5, 0.3), 0xf2eee0, 0.8, 0.75, 0);
    add(ci, Cy(0.14, 0.16, 0.2, 6), 0xf2eee0, 0.8, 1.6, 0);
    const bd = add(ci, new THREE.SphereGeometry(0.16, 6, 5), 0xc9a24b, 0.8, 1.82, 0, { metalness: 0.4, emissive: 0x2a1c06 });
    bd.scale.y = 1.3;
    win(ci, 0.16, 0.3, 0.04, 0, 0.45, 0.46);

    // scales (терези равноваги)
    const sg = new THREE.Group();
    sg.position.set(3.2, 0, 1.5);
    root.add(sg);
    add(sg, B(0.9, 0.5, 0.9), 0x8f8470, 0, 0.25, 0);
    add(sg, Cy(0.06, 0.08, 1.3, 6), 0xc9a24b, 0, 1.15, 0, { metalness: 0.4 });
    const bm = new THREE.Group();
    bm.position.y = 1.8;
    sg.add(bm);
    add(bm, B(1.5, 0.07, 0.07), 0xc9a24b, 0, 0, 0, { metalness: 0.4 });
    [-0.7, 0.7].forEach((x) => {
      add(bm, Cy(0.3, 0.18, 0.1, 8), 0xc9a24b, x, -0.55, 0, { metalness: 0.4, emissive: 0x2a1c06 });
      const pts: THREE.Vector3[] = [];
      [-0.25, 0.25].forEach((d) => {
        pts.push(new THREE.Vector3(x, 0, 0));
        pts.push(new THREE.Vector3(x + d, -0.5, 0));
      });
      bm.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0xe8c871 })));
    });
    const fin = new THREE.Mesh(new THREE.OctahedronGeometry(0.12), new THREE.MeshBasicMaterial({ color: 0xffe9a0 }));
    fin.position.y = 2.05;
    sg.add(fin);

    // mailbox
    const mb = new THREE.Group();
    mb.position.set(-3.35, 0, 2.85);
    mb.rotation.y = 0.6;
    root.add(mb);
    add(mb, B(0.1, 0.9, 0.1), 0x5a3a22, 0, 0.45, 0);
    add(mb, B(0.55, 0.32, 0.34), 0xc9a24b, 0, 1, 0, { metalness: 0.3 });
    add(mb, B(0.06, 0.28, 0.04), 0xb02a2a, 0.3, 1.2, 0);

    // books
    const bk = new THREE.Group();
    bk.position.set(-1, 0, 2.7);
    root.add(bk);
    [
      [0.55, 0.11, 0.38, 0x8a1f1f, 0, 0.06],
      [0.5, 0.1, 0.36, 0x2f5a3a, 0.15, 0.17],
      [0.46, 0.1, 0.34, 0xe9dcc0, -0.1, 0.27],
    ].forEach((q, i) => {
      const m = add(bk, B(q[0], q[1], q[2]), q[3], q[4], q[5], 0);
      m.rotation.y = (i - 1) * 0.35;
    });

    // cars
    const hlM = new THREE.MeshBasicMaterial({ color: 0xfff2c0 });
    const tlM = new THREE.MeshBasicMaterial({ color: 0xff3030 });
    const CAR: { g: THREE.Group; d: number; x: number; z: number; s: number; y: number }[] = [];
    const CCOL = [0xf2f2f2, 0x1f2024, 0xb03030, 0x7d8590, 0xe8c030, 0x2b4a8a, 0xdddddd, 0x3a3a3a];
    CCOL.forEach((c, i) => {
      const g = new THREE.Group();
      add(g, B(0.3, 0.1, 0.62), c, 0, 0.1, 0);
      add(g, B(0.26, 0.09, 0.3), 0x2c3a44, 0, 0.19, -0.04);
      [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach((w) => {
        add(g, Cy(0.06, 0.06, 0.05, 8), 0x111114, w[0] * 0.16, 0.06, w[1] * 0.2).rotation.z = 1.5708;
      });
      [-0.1, 0.1].forEach((x) => {
        const h = new THREE.Mesh(B(0.06, 0.04, 0.02), hlM);
        h.position.set(x, 0.11, 0.32);
        g.add(h);
        const t = new THREE.Mesh(B(0.06, 0.04, 0.02), tlM);
        t.position.set(x, 0.11, -0.32);
        g.add(t);
      });
      const d = i % 2 ? -1 : 1;
      g.rotation.y = d > 0 ? 0 : Math.PI;
      root.add(g);
      CAR.push({ g, d, x: d > 0 ? -4.55 : -5.25, z: -5 + (i >> 1) * 3.4, s: 0.8 + rnd() * 0.6, y: 0.035 });
    });

    // people
    const DOORX = [-0.2, 0.3, 0.8, 1.3, 1.8];
    const SPN = [[-3.3, 3.1], [-3.3, 1.8], [2.6, 5.5], [4.3, 2.7], [4.4, 0.8], [-1.6, 3.3], [3.9, 3.2]];
    const PL: { g: THREE.Group; lg: THREE.Group[]; pts: [number, number][]; i: number; x: number; z: number; sp: number; st: number; wt: number; inb: boolean; sc: number; ph: number; visible: boolean }[] = [];
    function mkPath() {
      const sp = SPN[Math.floor(rnd() * SPN.length)] as [number, number];
      const dx = DOORX[Math.floor(rnd() * 5)];
      const p: [number, number][] = [sp];
      if (sp[0] === 2.6) p.push([2.6, 3.7]);
      p.push([dx + (rnd() - 0.5) * 0.8, 0.2 + rnd() * 0.7], [dx, -0.7], [dx, -1.65], [dx, -2.2]);
      return p;
    }
    for (let i = 0; i < 16; i++) {
      const g = new THREE.Group();
      const sh = [0x2a3a5a, 0x5a2a2a, 0x2f4f3a, 0x4a4a4a, 0x8a6a3a, 0x1f1f24, 0xdddddd][Math.floor(rnd() * 7)];
      add(g, Cy(0.05, 0.06, 0.2, 6), sh, 0, 0.27, 0);
      add(g, new THREE.SphereGeometry(0.045, 6, 5), 0xd8b08a, 0, 0.43, 0);
      const lg = [-1, 1].map((s) => {
        const q = new THREE.Group();
        q.position.set(s * 0.03, 0.17, 0);
        g.add(q);
        add(q, B(0.032, 0.17, 0.04), 0x1d1d22, 0, -0.08, 0);
        return q;
      });
      root.add(g);
      const p = {
        g,
        lg,
        pts: mkPath(),
        i: 1,
        x: 0,
        z: 0,
        sp: 0.35 + rnd() * 0.2,
        st: 1,
        wt: rnd() * 6,
        inb: true,
        sc: 0,
        ph: rnd() * 6,
        visible: false,
      };
      p.x = p.pts[0][0];
      p.z = p.pts[0][1];
      g.visible = false;
      PL.push(p);
    }

    // fireflies, stars, moon, city silhouette
    const FN = 30;
    const fp = new Float32Array(FN * 3);
    const fb: { a: number; r: number; y: number; s: number; o: number }[] = [];
    for (let i = 0; i < FN; i++) {
      const a = rnd() * 6.28;
      const r = 1 + rnd() * 5;
      fb.push({ a, r, y: 0.5 + rnd() * 2.3, s: 0.3 + rnd() * 0.5, o: rnd() * 6 });
    }
    const fg = new THREE.BufferGeometry();
    fg.setAttribute("position", new THREE.BufferAttribute(fp, 3));
    const ffM = new THREE.PointsMaterial({ color: 0xe8e27a, size: 0.09, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
    root.add(new THREE.Points(fg, ffM));

    const sp2 = new Float32Array(180 * 3);
    for (let i = 0; i < 180; i++) {
      const a = rnd() * 6.28;
      const e = 0.2 + rnd() * 1.2;
      const rr = 60;
      sp2[i * 3] = Math.sin(a) * Math.cos(e) * rr;
      sp2[i * 3 + 1] = Math.sin(e) * rr;
      sp2[i * 3 + 2] = Math.cos(a) * Math.cos(e) * rr;
    }
    const sg2 = new THREE.BufferGeometry();
    sg2.setAttribute("position", new THREE.BufferAttribute(sp2, 3));
    const stM = new THREE.PointsMaterial({ color: 0xcfd8ff, size: 0.35, fog: false, transparent: true, opacity: 0.7 });
    S.add(new THREE.Points(sg2, stM));

    const mo = new THREE.Mesh(new THREE.SphereGeometry(2, 16, 12), new THREE.MeshBasicMaterial({ color: 0xe9eeff, fog: false }));
    mo.position.set(-30, 28, -34);
    S.add(mo);

    const SKM = new THREE.MeshBasicMaterial({ color: 0x14121a, fog: false });
    for (let i = 0; i < 70; i++) {
      const a = (i / 70) * 6.2832 + rnd() * 0.05;
      const r = 30 + rnd() * 6;
      const h = 1 + rnd() * 3.5;
      const m = new THREE.Mesh(B(1 + rnd() * 1.6, h, 1 + rnd() * 1.2), SKM);
      m.position.set(Math.sin(a) * r, h / 2 - 1.2, Math.cos(a) * r);
      S.add(m);
    }

    const LP = 260;
    const lpp = new Float32Array(LP * 3);
    for (let i = 0; i < LP; i++) {
      const a = rnd() * 6.28;
      const r = 29 + rnd() * 7;
      lpp[i * 3] = Math.sin(a) * r;
      lpp[i * 3 + 1] = -1 + rnd() * 3.5;
      lpp[i * 3 + 2] = Math.cos(a) * r;
    }
    const lpg = new THREE.BufferGeometry();
    lpg.setAttribute("position", new THREE.BufferAttribute(lpp, 3));
    const lpM = new THREE.PointsMaterial({ color: 0xffd27a, size: 0.28, fog: false, transparent: true, opacity: 0.85 });
    S.add(new THREE.Points(lpg, lpM));

    [
      [-6, -11],
      [0, -12.5],
      [6, -11],
    ].forEach((p) => {
      const g = new THREE.Group();
      g.position.set(p[0], 0, p[1]);
      S.add(g);
      [
        [-0.25, -0.25],
        [0.25, -0.25],
        [-0.25, 0.25],
        [0.25, 0.25],
      ].forEach((q) => {
        const l = new THREE.Mesh(B(0.06, 6.5, 0.06), new THREE.MeshBasicMaterial({ color: 0x6f757c }));
        l.position.set(q[0] * 1.4, 3.2, q[1] * 1.4);
        g.add(l);
      });
      const hd = new THREE.Mesh(B(1.1, 0.5, 0.2), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
      hd.position.y = 6.6;
      g.add(hd);
    });

    const mp = new THREE.Group();
    mp.position.set(-8.5, 0, -9);
    S.add(mp);
    const mw = new THREE.Mesh(B(1.5, 0.9, 1.3), new THREE.MeshBasicMaterial({ color: 0xe5d9b3 }));
    mw.position.y = 0.45;
    mp.add(mw);
    const mr2 = new THREE.Mesh(Co(1.1, 0.5, 4), new THREE.MeshBasicMaterial({ color: 0x9a2f2a }));
    mr2.position.y = 1.15;
    mr2.rotation.y = 0.785;
    mp.add(mr2);

    // Hotspot groups + meshes for picking
    const HS = hotspots.map((h) => ({ ...h, group: null as THREE.Group | null }));
    HS.forEach((h) => {
      const g = new THREE.Group();
      g.position.set(h.position[0], h.position[1], h.position[2]);
      root.add(g);
      h.group = g;

      // proxy mesh for picking
      const proxy = new THREE.Mesh(new THREE.SphereGeometry(h.radius, 16, 16), new THREE.MeshBasicMaterial({ visible: false }));
      proxy.userData.key = h.key;
      root.add(proxy);
      hotspotMeshesRef.current.push(proxy);
    });

    // UI overlay (rendered by React above canvas), but we need the canvas to fill area
    const RM = window.matchMedia("(prefers-reduced-motion:reduce)").matches;

    const SKYD = new THREE.Color(0xaec4da);
    const SKYN = new THREE.Color(0x0b0b14);
    const HSD = new THREE.Color(0xdbe9ff);
    const HSN = new THREE.Color(0x6a7aa8);
    const HGD = new THREE.Color(0x6f7a52);
    const HGN = new THREE.Color(0x3a2a1c);
    const SND = new THREE.Color(0xfff0cf);
    const SNN = new THREE.Color(0x9db4ff);
    const SKD = new THREE.Color(0x9fb0c4);
    const SKN2 = new THREE.Color(0x14121a);
    const WD = new THREE.Color(0x3d8fb5);
    const WN2 = new THREE.Color(0x1d4a6e);
    const gcol = new THREE.Color(0x7f9bb3);

    function wnd(M: THREE.InstancedMesh, N: number, o: number[], t: number, i0: number) {
      for (let i = 0; i < N; i++) {
        const f = (RM ? 1 : 0.82 + 0.18 * Math.sin(t * 1.7 + i * 2.9 + i0) * Math.sin(t * 0.5 + i * 1.3)) * o[i];
        const nd = 1 - stateRef.current.day;
        M.setColorAt(i, cc.setRGB(gcol.r * stateRef.current.day * 0.9 + f * nd, gcol.g * stateRef.current.day * 0.9 + 0.72 * f * nd, gcol.b * stateRef.current.day * 0.9 + 0.35 * f * nd));
      }
      if (M.instanceColor) M.instanceColor.needsUpdate = true;
    }

    const clk = new THREE.Clock();
    function loop() {
      const dt = Math.min(0.05, clk.getDelta());
      const t = clk.elapsedTime;
      const k = Math.min(1, dt * (RM ? 30 : 4));

      stateRef.current.day += (stateRef.current.dayT - stateRef.current.day) * Math.min(1, dt * (RM ? 30 : 1.6));
      const nd = 1 - stateRef.current.day;

      stateRef.current.idle += dt;
      if (!RM && stateRef.current.sel < 0 && stateRef.current.idle > 4) {
        stateRef.current.goal.y += dt * 0.09;
      }

      const cur = stateRef.current.cur;
      const goal = stateRef.current.goal;
      cur.y += (goal.y - cur.y) * k;
      cur.p += (goal.p - cur.p) * k;
      cur.r += (goal.r - cur.r) * k;
      cur.t.lerp(goal.t, k);

      const C = cameraRef.current;
      if (C) {
        C.position.set(
          cur.t.x + cur.r * Math.sin(cur.y) * Math.cos(cur.p),
          cur.t.y + cur.r * Math.sin(cur.p),
          cur.t.z + cur.r * Math.cos(cur.y) * Math.cos(cur.p),
        );
        C.lookAt(cur.t);
      }

      if (S.background instanceof THREE.Color) {
        S.background.copy(SKYN).lerp(SKYD, stateRef.current.day);
        if (S.fog) S.fog.color.copy(S.background);
      }
      hemi.color.copy(HSN).lerp(HSD, stateRef.current.day);
      hemi.groundColor.copy(HGN).lerp(HGD, stateRef.current.day);
      hemi.intensity = 0.8 + 0.35 * stateRef.current.day;
      moon.color.copy(SNN).lerp(SND, stateRef.current.day);
      moon.intensity = 0.95 + 0.3 * stateRef.current.day;
      // Simplified: no stars/moon/silhouette/fireflies rendering (performance)
      (water.material as THREE.MeshStandardMaterial).color.copy(WN2).lerp(WD, stateRef.current.day);

      glow.forEach((m, i) => {
        const f = RM ? 1 : 0.84 + 0.16 * Math.sin(t * 2.1 + i * 2.3) * Math.sin(t * 0.7 + i * 1.3);
        const q = 0.2 + 0.8 * nd;
        (m as THREE.MeshBasicMaterial).color.setRGB(f * q, 0.72 * f * q, 0.35 * f * q);
      });

      wnd(WM, WN, wo, t, 0);
      wnd(NM, NN, no, t, 5);

      (pl0 as THREE.PointLight).intensity = (1.25 + (RM ? 0 : 0.12 * Math.sin(t * 2.3))) * (0.05 + 0.95 * nd);
      (pl1 as THREE.PointLight).intensity = (1 + (RM ? 0 : 0.15 * Math.sin(t * 1.1))) * (0.05 + 0.95 * nd);

      stateRef.current.doorF = Math.max(0, stateRef.current.doorF - dt * 1.5);
      dmat.emissiveIntensity = 0.7 * nd + stateRef.current.doorF * 1.2;
      hlM.color.setRGB(1, 0.95, 0.75).multiplyScalar(0.35 + 0.65 * nd);

      (water.material as THREE.MeshStandardMaterial).emissiveIntensity = RM ? 1 : 0.9 + 0.35 * Math.sin(t * 0.8);

      rip.forEach((r) => {
        r.m.position.x += r.s * dt;
        if (r.m.position.x > 6) r.m.position.x = -6;
      });

      [fT, fB].forEach((f) => {
        const p = f.geometry.attributes.position as THREE.BufferAttribute;
        const b = (f as any).userData.b;
        for (let i = 0; i < p.count; i++) {
          const x = b[i * 3];
          p.array[i * 3 + 2] = RM ? 0 : Math.sin(x * 9 - t * 5) * 0.035 * (x / 0.5);
        }
        p.needsUpdate = true;
      });

      CAR.forEach((c) => {
        c.z += c.d * c.s * dt;
        if (c.d > 0 && c.z > 6.3) {
          c.z = -6.3;
          c.s = 0.8 + rnd() * 0.6;
        }
        if (c.d < 0 && c.z < -6.3) {
          c.z = 6.3;
          c.s = 0.8 + rnd() * 0.6;
        }
        const yb = c.z > 3.3 && c.z < 5.6 ? 0.16 : 0.035;
        c.y += (yb - c.y) * Math.min(1, dt * 8);
        const sc = 1.25 * Math.max(0.01, Math.min(1, (5.9 - Math.abs(c.z)) / 0.6));
        c.g.scale.setScalar(sc);
        c.g.position.set(c.x, c.y, c.z);
      });

      PL.forEach((p) => {
        if (p.st) {
          p.wt -= dt;
          if (p.wt <= 0) {
            if (p.inb) {
              p.pts = p.pts.slice().reverse();
              p.inb = false;
            } else {
              p.pts = mkPath();
              p.inb = true;
            }
            p.x = p.pts[0][0];
            p.z = p.pts[0][1];
            p.i = 1;
            p.st = 0;
            p.sc = 0;
            p.g.visible = true;
          }
          return;
        }
        const q = p.pts[p.i];
        const dx = q[0] - p.x;
        const dz = q[1] - p.z;
        const d = Math.hypot(dx, dz);
        const st = p.sp * dt;
        if (d <= st) {
          p.x = q[0];
          p.z = q[1];
          p.i++;
        } else {
          p.x += (dx / d) * st;
          p.z += (dz / d) * st;
          p.g.rotation.y = Math.atan2(dx, dz);
        }
        const last = p.pts[p.pts.length - 1];
        const first = p.pts[0];
        const dl = Math.hypot(p.x - (p.inb ? last[0] : first[0]), p.z - (p.inb ? last[1] : first[1]));
        const ts = (p.inb ? Math.min(1, dl / 0.5) : 1) * (!p.inb ? Math.min(1, Math.hypot(p.x - first[0], p.z - first[1]) / 0.5) : 1);
        p.sc += (ts - p.sc) * Math.min(1, dt * 8);
        p.g.scale.setScalar(1.35 * Math.max(0.01, p.sc));
        const w = t * 7 * p.sp / 0.4 + p.ph;
        p.lg[0].rotation.x = Math.sin(w) * 0.6;
        p.lg[1].rotation.x = -Math.sin(w) * 0.6;
        p.g.position.set(p.x, ground(p.x, p.z) + Math.abs(Math.sin(w)) * 0.008, p.z);

        if (p.i >= p.pts.length) {
          p.st = 1;
          p.wt = 0.8 + rnd() * 2.5;
          p.g.visible = false;
          if (p.inb) stateRef.current.doorF = 1;
        }
      });

      TR.forEach((o) => {
        o.m.rotation.z = RM ? 0 : 0.04 * Math.sin(t * 0.9 + o.p);
      });
      if (bm) {
        (bm as any).rotation.z = RM ? 0 : 0.14 * Math.sin(t * 0.9);
      }
      fin.rotation.y = t;
      fin.position.y = 2.05 + Math.sin(t * 1.5) * 0.04;

      for (let i = 0; i < FN; i++) {
        const o = fb[i];
        const a = o.a + t * 0.05 * o.s;
        fp[i * 3] = Math.sin(a) * o.r + Math.sin(t * o.s + o.o) * 0.3;
        fp[i * 3 + 1] = o.y + Math.sin(t * o.s * 1.3 + o.o) * 0.35;
        fp[i * 3 + 2] = Math.cos(a) * o.r;
      }
      fg.attributes.position.needsUpdate = true;

      HS.forEach((h, i) => {
        const on = i === stateRef.current.hov || i === stateRef.current.sel;
        const ts = on ? 1.03 : 1;
        h.sc = h.sc || 1;
        h.sc += (ts - h.sc) * Math.min(1, dt * 10);
        if (h.group) h.group.scale.setScalar(h.sc);
      });

      if (C) R.render(S, C);
      rafRef.current = requestAnimationFrame(loop);
    }

    // Pointer events
    const onPointerDown = (e: PointerEvent) => {
      canvas.setPointerCapture(e.pointerId);
      stateRef.current.drag = { x: e.clientX, y: e.clientY, mv: 0 };
      canvas.style.cursor = "grabbing";
      stateRef.current.idle = 0;
    };

    const onPointerMove = (e: PointerEvent) => {
      const drag = stateRef.current.drag;
      if (drag) {
        const dx = e.clientX - drag.x;
        const dy = e.clientY - drag.y;
        drag.mv += Math.abs(dx) + Math.abs(dy);
        drag.x = e.clientX;
        drag.y = e.clientY;
        stateRef.current.goal.y -= dx * 0.006;
        stateRef.current.goal.p = Math.max(0.15, Math.min(1.25, stateRef.current.goal.p + dy * 0.004));
        stateRef.current.idle = 0;
        const tip = document.getElementById("iu-tip");
        if (tip) tip.style.opacity = "0";
      } else {
        const k = pick(e.clientX, e.clientY);
        stateRef.current.hov = k;
        canvas.style.cursor = k > -1 ? "pointer" : "grab";
        const tip = document.getElementById("iu-tip");
        if (tip) {
          if (k > -1) {
            tip.textContent = hotspots[k].name;
            tip.style.left = e.clientX + 16 + "px";
            tip.style.top = e.clientY + 10 + "px";
            tip.style.opacity = "1";
          } else {
            tip.style.opacity = "0";
          }
        }
      }
    };

    const onPointerUp = (e: PointerEvent) => {
      canvas.style.cursor = "grab";
      const m = stateRef.current.drag && stateRef.current.drag.mv;
      stateRef.current.drag = null;
      if (m && m < 6) {
        const k = pick(e.clientX, e.clientY);
        if (k > -1) {
          selectHotspot(k);
        } else if (stateRef.current.sel > -1) {
          backFromHotspot();
        }
      }
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      stateRef.current.goal.r = Math.max(5, Math.min(26, stateRef.current.goal.r * (1 + e.deltaY * 0.0012)));
    };

    const onResize = () => {
      const C = cameraRef.current;
      const R = rendererRef.current;
      const canvas = canvasRef.current;
      if (!C || !R || !canvas) return;
      C.aspect = window.innerWidth / window.innerHeight;
      C.updateProjectionMatrix();
      R.setSize(window.innerWidth, window.innerHeight);
    };

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") backFromHotspot();
    });

    rendererRef.current = R;
    sceneRef.current = S;
    cameraRef.current = C;

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", (e) => {
        if (e.key === "Escape") backFromHotspot();
      });
      R.dispose?.();
    };
  }, []);

  return (
    <div ref={containerRef} className={`relative ${className}`} style={{ height, width: "100%", background: "#0c0a0b" }}>
      <div id="ai-ugoda-scene-ui" aria-hidden="true">
        <div className="iu-title">
          <h1>Київ. Площа Конституції</h1>
          <p>Верховна Рада, річка, міст, вулиця з рухом і люди біля входу. Кожен предмет — розділ сайту.</p>
        </div>
        <div className="iu-hint">Тягніть: обертати · Колесо: наближення · Клік по предмету: розділ</div>
        <button className="iu-night-btn" onClick={toggleDayNight} aria-label="День / ніч">
          {isNight ? "День" : "Ніч"}
        </button>
        <div id="iu-tip" className="iu-tip" />
      </div>
      <div className="iu-vg" aria-hidden="true" />
      <canvas id="ai-ugoda-scene-canvas" ref={canvasRef} aria-label="Інтерактивна 3D-сценка площі Конституції" />
      <div id="ai-ugoda-scene-err" className="iu-err" aria-live="polite">
        Не вдалося запустити 3D (потрібен WebGL і доступ до three.js).
      </div>
      {cardOpen && cardData && (
        <div className={`iu-card ${cardData.status === "ok" ? "" : ""} ${cardOpen ? "on" : ""}`} role="dialog" aria-modal="true" aria-label={cardData.name}>
          <h2>{cardData.name}</h2>
          <div className="iu-sec">{cardData.section}</div>
          <p>{cardData.desc}</p>
          <span className={`iu-badge ${cardData.status}`}>{cardData.statusText}</span>
          <div className="iu-row">
            <button className="iu-btn p" onClick={() => {
              router.push(cardData.path);
              setCardOpen(false);
            }}>
              Відкрити розділ
            </button>
            <button className="iu-btn" onClick={backFromHotspot}>
              Назад
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
