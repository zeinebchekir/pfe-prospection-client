/**
 * Vue Router with navigation guards.
 */

import { createRouter, createWebHistory } from "vue-router"
import {useAuth} from "@/composables/useAuth"

// Timestamp of the last successful session verification
// Re-validate with backend every SESSION_TTL ms to detect expired tokens
const SESSION_TTL = 15 * 60 * 1000 // 15 minutes
let lastSessionCheck = 0

const routes = [
  // ───────────── PUBLIC ROUTES ─────────────

  {
    path: "/",
    name: "Landing",
    component: () => import("../pages/landingPage/LandingPage.vue"),
    meta: { requiresAuth: false },
  },

  {
    path: "/login",
    name: "Login",
    component: () => import("@/pages/LoginPage.vue"),
    meta: { requiresAuth: false, guestOnly: true },
  },

  {
    path: "/register",
    name: "Register",
    component: () => import("@/pages/RegisterPage.vue"),
    meta: { requiresAuth: false, guestOnly: true },
  },

  {
    path: "/reset-password",
    name: "ResetPassword",
    component: () => import("@/pages/ResetPasswordPage.vue"),
    meta: { requiresAuth: false, guestOnly: true },
  },

  // ───────────── GENERIC DASHBOARD ─────────────

  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true },
  },

  // ───────────── ROLE DASHBOARDS ─────────────

  {
    path: "/admin",
    name: "AdminDashboard",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },
  },
  {
    path: "/manager",
    name: "ManagerDashboard",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["CEO"] },
  },
  {
    path: "/commercial",
    name: "CommercialDashboard",
    component: () => import("@/pages/commercial/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },
  {
    path: "/admin/users",
    name: "UserManagement",
    component: () => import("@/pages/admin/UserManagement.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },
  },
  {
    path: "/admin/logs",
    name: "AuditLogs",
    component: () => import("@/pages/admin/AuditLogs.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },
  },
  {
    path: "/admin/monitoring-etl",
    name: "MonitoringETL",
    component: () => import("@/pages/admin/monitoringETLPipeline.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },

  },
  {
    path: "/admin/crm",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },
  },

  // ───────────── MANAGER SUB ROUTES ─────────────

  {
    path: "/manager/team",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["CEO"] },
  },
  {
    path: "/manager/sync",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["CEO"] },
  },
  {
    path: "/manager/reports",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["CEO"] },
  },

  // ───────────── COMMERCIAL SUB ROUTES ─────────────

  {
    path: "/commercial/prospects",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },
  {
    path: "/commercial/qualify",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },
  {
    path: "/commercial/sync",
    component: () => import("@/pages/DashboardPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },

  // ───────────── LEADS MODULE ─────────────

  {
    path: "/commercial/leads",
    name: "LeadsPage",
    component: () => import("@/pages/commercial/LeadsPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },
  {
    path: "/commercial/leads/:id",
    name: "LeadDetail",
    component: () => import("@/pages/commercial/LeadDetailPage.vue"),
    meta: { requiresAuth: true, roles: ["COMMERCIAL"] },
  },

  {
    path: "/profil",
    name: "Profile",
    component: () => import("@/pages/ProfilePage.vue"),
    meta: { requiresAuth: true },
  },

  // ───────────── 404 CATCH ALL ─────────────

  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/pages/NotFoundPage.vue"),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ───────────── NAVIGATION GUARD ─────────────

router.beforeEach(async (to) => {
  const { isAuthenticated, fetchUser, user } = useAuth()

  const requiresAuth = to.meta.requiresAuth === true
  const guestOnly    = to.meta.guestOnly === true
  const allowedRoles = to.meta.roles
  const now          = Date.now()

  // ── 1. First load OR session stale → verify with backend ──────────────
  // Always check on first navigation (user.value === null).
  // On subsequent navigations to protected routes, silently re-validate
  // every SESSION_TTL ms to catch expired tokens without disrupting UX.
  const isFirstLoad = user.value === null
  const isStale     = requiresAuth && (now - lastSessionCheck > SESSION_TTL)

  if (isFirstLoad || isStale) {
    await fetchUser()
    if (user.value !== null) {
      lastSessionCheck = now
    }
  }

  // ── 2. Not authenticated → redirect to login ──────────────────────────
  if (requiresAuth && !isAuthenticated.value) {
    return { name: "Login", query: { redirect: to.fullPath } }
  }

  // ── 3. Authenticated trying to access guest-only page ─────────────────
  if (guestOnly && isAuthenticated.value) {
    return getDashboardRedirect(user.value && user.value.role)
  }

  // ── 4. Role-based protection ───────────────────────────────────────────
  if (
    requiresAuth &&
    allowedRoles &&
    (!user.value || !allowedRoles.includes(user.value.role))
  ) {
    return getDashboardRedirect(user.value && user.value.role)
  }

  // ── 5. Redirect generic /dashboard to role-specific dashboard ────────
  if (to.name === "Dashboard" && isAuthenticated.value) {
    return getDashboardRedirect(user.value && user.value.role)
  }
})

// ───────────── HELPER ─────────────

function getDashboardRedirect(role) {
  switch (role) {
    case "ADMIN":
      return { name: "AdminDashboard" }
    case "CEO":
      return { name: "ManagerDashboard" }
    case "COMMERCIAL":
      return { name: "CommercialDashboard" }
    default:
      return { name: "Login" }
  }
}

export default router