<template>
  <div class="min-h-screen flex items-center justify-center bg-tacir-lightgray/30 p-6">
    <!-- Component switching based on "step" -->
    <RequestResetForm
      v-if="step === 'request'"
      @submitted="onResetRequested"
    />

    <SuccessMessage
      v-else-if="step === 'sent'"
      :email="email"
      @retry="step = 'request'"
    />

    <NewPasswordForm
      v-else-if="step === 'reset'"
      :token="token"
      @submitted="step = 'success'"
    />

    <SuccessMessage
      v-else-if="step === 'success'"
      is-final
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import RequestResetForm from '@/components/resetPassword/RequestResetForm.vue'
import SuccessMessage from '@/components/resetPassword/SuccessMessage.vue'
import NewPasswordForm from '@/components/resetPassword/NewPasswordForm.vue'

const route = useRoute()
const step  = ref<'request' | 'sent' | 'reset' | 'success'>('request')
const token = ref('')
const email = ref('')

onMounted(() => {
  // Check if token exists in URL (e.g. /reset-password?token=...)
  const queryToken = route.query.token as string
  if (queryToken) {
    token.value = queryToken
    step.value  = 'reset'
  }
})

function onResetRequested(targetEmail: string) {
  email.value = targetEmail
  step.value  = 'sent'
}
</script>
