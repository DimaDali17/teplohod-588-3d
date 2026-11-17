// NPC для модели теплохода пр. 588: простые фигурки, маршруты в корабельных координатах.
// X — от кормы, Y — от ДП (+ЛБ), Z — от ОП; в three.js: x = X - 47.9, y = Z, z = -Y.
import * as THREE from 'three';

const toV = (X, Y, Z) => new THREE.Vector3(X - 47.9, Z, -Y);
const sheer = (X) => 4.6 + (X > 80 ? 2.3 * ((X - 80) / 15.8) ** 2 : 0);

function rng(seed) { return () => (seed = (seed * 16807) % 2147483647) / 2147483647; }

const SKIN = [0xf1c8a8, 0xe0b090, 0xc99877, 0xf5d5bd];
const SHIRTS = [0x3b6ea8, 0xc0504d, 0x6aa84f, 0xe69138, 0x8e7cc3, 0xf1c232, 0x45818e, 0xffffff, 0xd5a6bd, 0x76a5af];
const PANTS = [0x2b2f3a, 0x4a4f5c, 0x6b5844, 0x1f3b5c, 0xd9d2c5];

export function createPeople(scene, meta, clips) {
  const rand = rng(588);
  const pick = (a) => a[Math.floor(rand() * a.length)];
  const mats = new Map();
  const M = (c) => {
    if (!mats.has(c)) mats.set(c, new THREE.MeshStandardMaterial({ color: c, roughness: 0.8, clippingPlanes: clips }));
    return mats.get(c);
  };
  const legGeo = new THREE.BoxGeometry(0.14, 0.8, 0.16); legGeo.translate(0, -0.4, 0);
  const armGeo = new THREE.BoxGeometry(0.1, 0.6, 0.12); armGeo.translate(0, -0.3, 0);
  const torsoGeo = new THREE.BoxGeometry(0.42, 0.62, 0.25);
  const headGeo = new THREE.SphereGeometry(0.12, 12, 10);
  const people = [];

  function person({ name, deck, shirt, pants, skin, hat, seated, dress }) {
    const g = new THREE.Group();
    const legL = new THREE.Mesh(legGeo, M(pants)); legL.position.set(-0.11, 0.82, 0);
    const legR = new THREE.Mesh(legGeo, M(pants)); legR.position.set(0.11, 0.82, 0);
    const torso = new THREE.Mesh(torsoGeo, M(shirt)); torso.position.y = 1.13;
    const armL = new THREE.Mesh(armGeo, M(shirt)); armL.position.set(-0.27, 1.42, 0);
    const armR = new THREE.Mesh(armGeo, M(shirt)); armR.position.set(0.27, 1.42, 0);
    const head = new THREE.Mesh(headGeo, M(skin ?? pick(SKIN))); head.position.y = 1.6;
    g.add(legL, legR, torso, armL, armR, head);
    if (dress) {
      const sk = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.3, 0.5, 10), M(shirt)); sk.position.y = 0.6; g.add(sk);
    }
    if (hat === 'captain') {
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.13, 0.08, 14), M(0xffffff)); cap.position.y = 1.74;
      const band = new THREE.Mesh(new THREE.CylinderGeometry(0.131, 0.131, 0.03, 14), M(0x111111)); band.position.y = 1.705;
      const visor = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.02, 0.1), M(0x111111)); visor.position.set(0, 1.7, 0.14);
      g.add(cap, band, visor);
    } else if (hat === 'sailor') {
      const b = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.12, 0.06, 12), M(0xffffff)); b.position.y = 1.73; g.add(b);
    } else if (hat === 'chef') {
      const b = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.1, 0.22, 12), M(0xffffff)); b.position.y = 1.8; g.add(b);
    }
    if (seated) {
      legL.rotation.x = legR.rotation.x = -Math.PI / 2;
      armL.rotation.x = armR.rotation.x = -0.9;
    }
    g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.userData.npc = name; } });
    scene.add(g);
    const p = { g, legL, legR, armL, armR, name, deck, seated, phase: rand() * 6 };
    people.push(p);
    return p;
  }

  function walker(opts, pts, { speed = 1.1, loop = false, start = 0 } = {}) {
    const p = person(opts);
    const path = pts.map(([X, Y, Z]) => toV(X, Y, Z));
    if (!loop) for (let i = path.length - 2; i > 0; i--) path.push(path[i].clone());
    const seg = [];
    let total = 0;
    for (let i = 0; i < path.length; i++) {
      const a = path[i], b = path[(i + 1) % path.length];
      const l = a.distanceTo(b); seg.push({ a, b, l }); total += l;
    }
    Object.assign(p, { path: seg, total, s: start * total, speed });
    return p;
  }

  function sitter(opts, seat) {
    const p = person({ ...opts, seated: !seat.staff });
    const v = new THREE.Vector3(...seat.pos);
    p.g.position.copy(v);
    if (!seat.staff) p.g.position.y -= 0.37;
    if (seat.table) {
      const t = new THREE.Vector3(...seat.table);
      p.g.rotation.y = Math.atan2(t.x - v.x, t.z - v.z);
    } else {
      p.g.rotation.y = Math.atan2(Math.cos(seat.rot), -Math.sin(seat.rot));
    }
    return p;
  }

  const guest = (deck, name = 'Пассажир') => {
    const female = rand() < 0.5;
    return { name: female ? 'Пассажирка' : name, deck, shirt: pick(SHIRTS), pants: pick(PANTS), dress: female && rand() < 0.6 };
  };

  // --- экипаж ---
  walker({ name: 'Капитан', deck: 'roof', shirt: 0xffffff, pants: 0x1a1f2b, hat: 'captain' },
    [[66.2, 3.6, 12.5], [69.4, 3.6, 12.5], [69.4, -3.6, 12.5], [66.2, -3.6, 12.5]], { speed: 0.7, loop: true });
  const helm = person({ name: 'Рулевой', deck: 'roof', shirt: 0x1f3b5c, pants: 0x1a1f2b, hat: 'sailor' });
  helm.g.position.copy(toV(75.0, 0, 12.5)); helm.g.rotation.y = Math.PI / 2;
  walker({ name: 'Матрос', deck: 'main', shirt: 0x1f3b5c, pants: 0x1a1f2b, hat: 'sailor' },
    [[89.4, 1.9, sheer(89.4)], [92.4, 1.9, sheer(92.4)], [92.4, -1.9, sheer(92.4)], [89.4, -1.9, sheer(89.4)]], { speed: 0.6, loop: true });
  walker({ name: 'Официант', deck: 'main', shirt: 0xffffff, pants: 0x111111 },
    [[78.6, -1.2, 4.68], [86.2, -1.2, 4.68], [86.2, 1.2, 4.68], [78.6, 1.2, 4.68]], { speed: 0.9, loop: true });
  walker({ name: 'Официантка', deck: 'boat', shirt: 0xffffff, pants: 0x111111, dress: true },
    [[68.4, -1.2, 9.98], [75.0, -1.2, 9.98], [75.0, 1.2, 9.98], [68.4, 1.2, 9.98]], { speed: 0.9, loop: true, start: 0.5 });
  walker({ name: 'Повар', deck: 'main', shirt: 0xffffff, pants: 0x777777, hat: 'chef' },
    [[69.2, -3.2, 4.68], [76.5, -3.2, 4.68]], { speed: 0.5 });

  // --- пассажиры на прогулке ---
  const strolls = [
    ['main', 6.6, 14, 77, 4.6], ['main', -6.6, 14, 77, 4.6],
    ['mid', 5.8, 10, 86, 7.32], ['mid', -5.8, 10, 86, 7.32],
    ['boat', 5.4, 34, 64, 9.92], ['boat', -5.4, 34, 64, 9.92],
  ];
  for (const [deck, Y, x0, x1, Z] of strolls) {
    const n = deck === 'boat' ? 1 : 2;
    for (let k = 0; k < n; k++)
      walker(guest(deck), [[x0, Y, Z], [x1, Y, Z]], { speed: 0.8 + rand() * 0.5, start: rand() });
  }
  walker(guest('roof'), [[22, 3.0, 12.5], [55, 3.0, 12.5], [55, -3.0, 12.5], [22, -3.0, 12.5]], { speed: 0.9, loop: true });
  walker(guest('roof'), [[22, 3.0, 12.5], [55, 3.0, 12.5], [55, -3.0, 12.5], [22, -3.0, 12.5]], { speed: 0.9, loop: true, start: 0.04 });
  walker(guest('main'), [[36.5, 1.6, 4.68], [55.5, 1.6, 4.68]], { speed: 0.8, start: 0.3 });
  walker(guest('lower'), [[47, 2.2, 1.98], [68, 2.2, 1.98]], { speed: 0.8, start: 0.6 });

  // --- сидящие ---
  for (const s of meta.seats) {
    if (s.staff) { sitter({ name: s.staff, deck: s.deck, shirt: 0xffffff, pants: 0x111111 }, s); continue; }
    const crew = s.room === 'Кают-компания';
    const chance = crew ? 0.5 : (s.room.startsWith('Дискозал') ? 0.3 : 0.5);
    if (rand() > chance) continue;
    sitter(crew ? { name: 'Член экипажа', deck: s.deck, shirt: 0x1f3b5c, pants: 0x1a1f2b } : guest(s.deck), s);
  }

  const tmp = new THREE.Vector3();
  function update(dt) {
    for (const p of people) {
      if (!p.path || !p.g.visible) continue;
      p.s = (p.s + p.speed * dt) % p.total;
      let s = p.s, i = 0;
      while (s > p.path[i].l) { s -= p.path[i].l; i++; }
      const { a, b, l } = p.path[i];
      tmp.lerpVectors(a, b, l ? s / l : 0);
      p.g.position.copy(tmp);
      p.g.rotation.y = Math.atan2(b.x - a.x, b.z - a.z);
      p.phase += dt * p.speed * 5.5;
      const sw = Math.sin(p.phase) * 0.55;
      p.legL.rotation.x = sw; p.legR.rotation.x = -sw;
      p.armL.rotation.x = -sw * 0.7; p.armR.rotation.x = sw * 0.7;
    }
  }
  return { people, update };
}
