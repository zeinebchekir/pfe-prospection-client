/**
 * Vue Router with navigation guards.
 *
 * Route access is controlled via meta fields:
 *   requiresAuth: true   — user must be authenticated
 *   guestOnly: true      — authenticated users are redirected away (e.g. /login)
 *   roles: ["ADMIN"]     — only users with these roles can access the route
 *
 * IMPORTANT: These guards are UI-only. Backend APIs enforce their own permissions.
 */

import { createRouter, createWebHistory } from "vue-router"
import {useAuth} from "@/composables/useAuth"

// Re-validate the session with the backend every SESSION_TTL ms on protected routes.
// This catches expired tokens without polling continuously.
// On first load (user === null), validation always happens regardless of this interval.
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
    path: "/admin/reports",
    name: "ReportsList",
    component: () => import("@/pages/admin/ReportsList.vue"),
    meta: { requiresAuth: true, roles: ["ADMIN"] },
  },
  {
    path: "/admin/etllogs",
    name: "ETLLogsViewer",
    component: () => import("@/pages/admin/ETLLogs.vue"),
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
  {
    path: "/manager/segmentation",
    name: "MarketAnalysis",
    component: () => import("@/pages/manager/MarketAnalysisPage.vue"),
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
  {
    path: "/commercial/analyse-results",
    name: "AnalyseResults",
    component: () => import("@/pages/commercial/AnalyseResultsPage.vue"),
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
    path: "/commercial/opportunities",
    name: "OpportunityLeadsPage",
    component: () => import("@/pages/commercial/OpportunityLeadsPage.vue"),
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
  const allowedRoles = to.meta.roles  // undefined means any authenticated user is allowed
  const now          = Date.now()

  // ── 1. First load OR session stale → verify with backend ──────────────
  // Always call fetchUser() on first navigation (user.value === null).
  // On subsequent protected-route navigations, silently re-validate every SESSION_TTL
  // to catch expired tokens without disrupting the user experience.
  const isFirstLoad = user.value === null
  const isStale     = requiresAuth && (now - lastSessionCheck > SESSION_TTL)

  if (isFirstLoad || isStale) {
    await fetchUser()  // GET /api/auth/me/ — silently restores session from cookie
    if (user.value !== null) {
      lastSessionCheck = now  // Reset timer only on successful verification
    }
  }

  // ── 2. Not authenticated → redirect to login ──────────────────────────
  // Preserve the intended destination so the login page can redirect back after auth.
  if (requiresAuth && !isAuthenticated.value) {
    return { name: "Login", query: { redirect: to.fullPath } }
  }

  // ── 3. Authenticated user on guest-only page → send to dashboard ─────
  // Prevents logged-in users from seeing /login or /register again.
  if (guestOnly && isAuthenticated.value) {
    return getDashboardRedirect(user.value && user.value.role)
  }

  // ── 4. Role mismatch → redirect to own dashboard ─────────────────────
  // No "Access Denied" page is shown — users are silently redirected.
  // This is a UX choice; the backend independently enforces permissions.
  if (
    requiresAuth &&
    allowedRoles &&
    (!user.value || !allowedRoles.includes(user.value.role))
  ) {
    return getDashboardRedirect(user.value && user.value.role)
  }

  // ── 5. Generic /dashboard → role-specific dashboard ────────────────
  // /dashboard is a neutral entry point; actual destination depends on role.
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
