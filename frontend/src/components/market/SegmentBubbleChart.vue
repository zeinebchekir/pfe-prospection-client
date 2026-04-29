<template>
  <div class="space-y-3">

    <!-- ── Main Bubble Chart ─────────────────────────────────── -->
    <div class="relative w-full" style="aspect-ratio: 16/7; min-height: 180px;">
      <svg
        :viewBox="`0 0 ${W} ${H}`"
        class="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
        style="cursor: default;"
      >
        <defs>
          <filter
            v-for="b in mainBubbles"
            :key="`f${b.key}`"
            :id="`shadow-${b.key}`"
            x="-30%" y="-30%" width="160%" height="160%"
          >
            <feDropShadow
              dx="0" dy="1.5" stdDeviation="2"
              :flood-color="b.color" flood-opacity="0.22"
            />
          </filter>
        </defs>

        <!-- ── Main segment bubbles ────────────────────────── -->
        <g
          v-for="b in mainBubbles"
          :key="b.key"
          style="cursor: pointer;"
          @click="toggleGroup(b.key)"
        >
          <!-- Outer pulse ring (animated when selected) -->
          <circle
            :cx="b.cx" :cy="b.cy"
            :r="b.r + (selectedGroup === b.key ? 2 : 0)"
            :fill="b.color"
            :fill-opacity="selectedGroup === b.key ? 0.08 : 0"
            :stroke="b.color"
            :stroke-width="selectedGroup === b.key ? 1.2 : 0.5"
            :stroke-opacity="selectedGroup === b.key ? 0.9 : 0.55"
            :filter="`url(#shadow-${b.key})`"
            style="transition: all 0.25s ease;"
          />
          <!-- Inner fill -->
          <circle
            :cx="b.cx" :cy="b.cy" :r="b.r * 0.6"
            :fill="b.color" :fill-opacity="selectedGroup === b.key ? 0.35 : 0.22"
            style="transition: fill-opacity 0.2s;"
          />
          <!-- Centre dot -->
          <circle
            :cx="b.cx" :cy="b.cy" :r="b.r * 0.12"
            :fill="b.color" fill-opacity="0.85"
          />

          <!-- Expand indicator ("+N" sub-segments) -->
          <text
            v-if="b.subCount > 1 && b.r >= 10"
            :x="b.cx + b.r * 0.75"
            :y="b.cy - b.r * 0.75"
            text-anchor="middle" dominant-baseline="middle"
            :font-size="Math.max(2.5, b.r * 0.20)"
            :fill="b.color" font-weight="700" opacity="0.85"
          >+{{ b.subCount }}</text>
        </g>

        <!-- Labels for all bubbles (using foreignObject for perfect flex stack) -->
        <g v-for="b in mainBubbles" :key="`lbl-${b.key}`" style="pointer-events:none;">
          <!-- Connector line for small bubbles (label outside) -->
          <line
            v-if="b.r < 10"
            :x1="b.cx + (b.lx > b.cx ? 1 : -1) * b.r * 0.92"
            :y1="b.cy"
            :x2="b.lx" :y2="b.ly"
            :stroke="b.color" stroke-width="0.35" stroke-opacity="0.45"
            stroke-dasharray="1.2,0.8"
          />
          
          <!-- Label container -->
          <!-- If large bubble (r>=10), text is centered INSIDE the bubble -->
          <foreignObject
            v-if="b.r >= 10"
            :x="b.cx - b.r" :y="b.cy - b.r"
            :width="b.r * 2" :height="b.r * 2"
            overflow="visible"
          >
            <div
              xmlns="http://www.w3.org/1999/xhtml"
              style="display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center;user-select:none;"
            >
              <div :style="{ fontSize: `${Math.max(3, b.r * 0.22)}px`, fontWeight: 700, color: b.color, lineHeight: 1.1 }">{{ b.key }}</div>
              <div :style="{ fontSize: `${Math.max(4, b.r * 0.3)}px`, fontWeight: 800, color: b.color, opacity: 0.85, marginTop: '1px', lineHeight: 1 }">{{ b.percent }}%</div>
              <div :style="{ fontSize: `${Math.max(2, b.r * 0.15)}px`, color: '#6b7280', marginTop: '1px', lineHeight: 1 }">{{ b.n }} leads</div>
            </div>
          </foreignObject>

          <!-- If small bubble (r<10), text is placed OUTSIDE via lx,ly -->
          <foreignObject
            v-else
            :x="b.lx - b.lw / 2" :y="b.ly - 5"
            :width="b.lw" height="15"
            overflow="visible"
          >
            <div
              xmlns="http://www.w3.org/1999/xhtml"
              style="display:flex;flex-direction:column;align-items:center;gap:0.5px;user-select:none;"
            >
              <div :style="{ fontSize: '3px', fontWeight: 700, color: b.color, whiteSpace:'nowrap', lineHeight: 1 }">{{ b.key }}</div>
              <div :style="{ fontSize: '2.5px', color: '#6b7280', whiteSpace:'nowrap', lineHeight: 1 }">{{ b.percent }}% · {{ b.n }} leads</div>
            </div>
          </foreignObject>
        </g>
      </svg>
    </div>

    <!-- ── Sub-segment drill-down panel ─────────────────────── -->
    <Transition name="slide-down">
      <div
        v-if="selectedGroup"
        class="rounded-xl border border-border bg-gray-50 p-4"
      >
        <!-- Panel header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <span
              class="w-2.5 h-2.5 rounded-full inline-block"
              :style="{ backgroundColor: activeColor }"
            />
            <span class="text-sm font-semibold text-tacir-darkblue">{{ selectedGroup }}</span>
            <span class="text-xs text-tacir-darkgray ml-1">
              — {{ activeTotal }} leads · cliquez sur un sous-segment pour explorer
            </span>
          </div>
          <button
            @click="selectedGroup = null"
            class="text-[11px] text-tacir-darkgray hover:text-tacir-darkblue flex items-center gap-1 px-2 py-1 rounded-lg border border-border hover:bg-white transition"
          >
            <X class="w-3 h-3" /> Fermer
          </button>
        </div>

        <!-- Sub-bubble mini-chart -->
        <div class="relative w-full" style="height: 160px;">
          <svg :viewBox="`0 0 ${subViewBoxWidth} 100`" class="w-full h-full" preserveAspectRatio="xMidYMid meet">
            <g v-for="sb in subBubbles" :key="sb.cluster">
              <circle
                :cx="sb.cx" :cy="sb.cy" :r="sb.r"
                :fill="sb.color" fill-opacity="0.15"
                :stroke="sb.color" stroke-width="0.5" stroke-opacity="0.6"
              />
              <circle :cx="sb.cx" :cy="sb.cy" :r="sb.r * 0.55" :fill="sb.color" fill-opacity="0.3" />
              <!-- Stats inside the bubble -->
              <text
                :x="sb.cx" :y="sb.cy - Math.min(2, sb.r * 0.1)"
                text-anchor="middle" dominant-baseline="middle"
                :font-size="Math.max(5, sb.r * 0.35)"
                font-weight="700" :fill="sb.color"
              >{{ sb.percent }}%</text>
              <text
                :x="sb.cx" :y="sb.cy + Math.max(4.5, sb.r * 0.3)"
                text-anchor="middle" dominant-baseline="middle"
                :font-size="Math.max(3.5, sb.r * 0.22)"
                fill="#4b5563" font-weight="500"
              >{{ sb.n }}</text>
              
              <!-- Label BELOW the bubble to prevent overlap -->
              <foreignObject
                :x="sb.cx - 38" :y="sb.cy + sb.r + 4"
                width="76" height="30"
                overflow="visible"
              >
                <div
                  xmlns="http://www.w3.org/1999/xhtml"
                  style="display:flex;justify-content:center;text-align:center;user-select:none;"
                >
                  <span :style="{ fontSize: '6.5px', fontWeight: 600, color: sb.color, lineHeight: 1.15 }">{{ sb.label_sub || 'Sous-segment' }}</span>
                </div>
              </foreignObject>
            </g>
          </svg>
        </div>

        <!-- Sub-segment stat pills -->
        <div class="flex flex-wrap gap-2 mt-2">
          <div
            v-for="sb in activeSubSegments"
            :key="sb.cluster"
            class="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-lg border bg-white"
            :style="{ borderColor: activeColor + '40' }"
          >
            <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: activeColor, opacity: 0.7 - 0.15 * activeSubSegments.indexOf(sb) }" />
            <span class="font-medium text-tacir-darkblue">{{ sb.label_sub || 'Sous-segment' }}</span>
            <span class="text-tacir-darkgray">{{ sb.n }} leads · {{ Math.round((sb.n / totalLeads) * 100) }}%</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── Hint text ─────────────────────────────────────────── -->
    <p class="text-[10px] text-tacir-darkgray/60 text-center">
      Cliquez sur un segment pour explorer ses sous-groupes
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { X } from "lucide-vue-next";

const W = 200;
const H = 76;

const props = defineProps({
  segments:   { type: Array,  default: () => [] },
  totalLeads: { type: Number, default: 0 },
});

// ── State: which main group is expanded ───────────────────────────────────────
const selectedGroup = ref(null);

function toggleGroup(key) {
  selectedGroup.value = selectedGroup.value === key ? null : key;
}

// ── Compute MERGED main-segment bubbles (by label_short) ─────────────────────
// Groups all clusters sharing the same label_short into one bubble.
const mainBubbles = computed(() => {
  if (!props.segments.length) return [];

  // 1. Aggregate by label_short
  const groupMap = new Map();
  for (const seg of props.segments) {
    const key = seg.label_short || seg.label;
    if (!groupMap.has(key)) {
      groupMap.set(key, { key, n: 0, color: seg.color, clusters: [] });
    }
    const g = groupMap.get(key);
    g.n += seg.n;
    g.clusters.push(seg);
  }

  const groups  = [...groupMap.values()].sort((a, b) => b.n - a.n);
  const maxN    = groups[0].n;
  const total   = props.totalLeads || groups.reduce((s, g) => s + g.n, 0);

  const RAW_MIN = 9, RAW_MAX = 26, GAP = 2;
  const items = groups.map((g) => ({
    ...g,
    r:        RAW_MIN + (g.n / maxN) * (RAW_MAX - RAW_MIN),
    percent:  Math.round((g.n / total) * 100),
    subCount: g.clusters.length,
  }));

  // 2. Spiral placement (same algorithm as before)
  const placed = [];
  for (let i = 0; i < items.length; i++) {
    const b = items[i];
    if (i === 0) {
      b.cx = W / 2; b.cy = H / 2;
    } else {
      let ok = false;
      outer:
      for (let dist = items[0].r + b.r + GAP; dist < W; dist += 1.5) {
        for (let a = 0; a < Math.PI * 2; a += Math.PI / 12) {
          const cx = W / 2 + dist * Math.cos(a);
          const cy = H / 2 + dist * Math.sin(a);
          if (cx - b.r < 2 || cx + b.r > W - 2) continue;
          if (cy - b.r < 2 || cy + b.r > H - 2) continue;
          let clear = true;
          for (const p of placed) {
            const d2 = (cx-p.cx)**2 + (cy-p.cy)**2;
            if (d2 < (p.r + b.r + GAP)**2) { clear = false; break; }
          }
          if (clear) { b.cx = cx; b.cy = cy; ok = true; break outer; }
        }
      }
      if (!ok) {
        b.cx = Math.min(W - b.r - 2, (placed.at(-1)?.cx ?? W/2) + b.r * 2 + 4);
        b.cy = H / 2;
      }
    }
    placed.push(b);
  }

  // 3. Label positions
  return placed.map((b) => {
    const dx   = b.cx - W/2, dy = b.cy - H/2;
    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const norm = { x: dx/dist, y: dy/dist };
    const out  = b.r < 10;
    return {
      ...b,
      lx: out ? b.cx + norm.x * (b.r + 9) : b.cx,
      ly: out ? b.cy + norm.y * (b.r + 9) : b.cy,
      lw: Math.max(30, b.key.length * 2.5),
    };
  });
});

// ── Active group metadata ────────────────────────────────────────────────────
const activeSubSegments = computed(() => {
  if (!selectedGroup.value) return [];
  return props.segments.filter(
    (s) => (s.label_short || s.label) === selectedGroup.value
  ).sort((a, b) => b.n - a.n);
});

const activeTotal = computed(() =>
  activeSubSegments.value.reduce((s, x) => s + x.n, 0)
);

const activeColor = computed(
  () => activeSubSegments.value[0]?.color ?? "#303E8C"
);

// ── Sub-segment mini bubbles (linear layout, simple) ─────────────────────────
const subViewBoxWidth = computed(() => {
  const count = activeSubSegments.value.length;
  if (!count) return 300;
  return Math.max(300, count * 90);
});

const subBubbles = computed(() => {
  const subs = activeSubSegments.value;
  if (!subs.length) return [];
  const total  = props.totalLeads || 1;
  const maxN   = subs[0].n;
  const step   = subViewBoxWidth.value / (subs.length + 1);

  return subs.map((s, i) => {
    const r = 14 + (s.n / maxN) * 18;
    return {
      ...s,
      cx: step * (i + 1),
      cy: 40,
      r,
      percent: Math.round((s.n / total) * 100),
    };
  });
});
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
