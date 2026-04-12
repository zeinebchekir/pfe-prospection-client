<template>
  <div class="min-h-screen bg-white font-sans">
    <TheNavbar />
    <HeroSection />
    <ProblemSection />
    <Separator class="bg-tacir-lightgray" />
    <SolutionsSection />
    <KpisSection />
    <SecuritySection />
    <CtaBand />
    <TheFooter />
  </div>
</template>

<script setup>
import { Separator } from '@/components/ui/separator'

import TheNavbar        from '../../components/landingPage/TheNavbar.vue'
import HeroSection      from '../../components/landingPage/HeroSection.vue'
import ProblemSection   from '../../components/landingPage/ProblemSection.vue'
import SolutionsSection from '../../components/landingPage/SolutionsSection.vue'
import KpisSection      from '../../components/landingPage/KpisSection.vue'
import SecuritySection  from '../../components/landingPage/SecuritySection.vue'
import CtaBand          from '../../components/landingPage/CtaBand.vue'
import TheFooter        from '../../components/landingPage/TheFooter.vue'
</script>
