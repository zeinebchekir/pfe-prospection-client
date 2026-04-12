<template>
  <span ref="elRef" class="tabular-nums">{{ count }}{{ suffix }}</span>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  target: { type: Number, required: true },
  suffix: { type: String, default: '' },
})

const count  = ref(0)
const elRef  = ref(null)
let started  = false
let observer = null

onMounted(() => {
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting && !started) {
        started = true
        let current = 0
        const duration  = 1500
        const step      = 16
        const increment = props.target / (duration / step)
        const timer = setInterval(() => {
          current += increment
          if (current >= props.target) {
            count.value = props.target
            clearInterval(timer)
          } else {
            count.value = Math.floor(current)
          }
        }, step)
      }
    },
    { threshold: 0.3 }
  )
  if (elRef.value) observer.observe(elRef.value)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>
