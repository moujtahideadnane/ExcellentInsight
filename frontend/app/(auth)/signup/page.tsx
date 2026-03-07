"use client"

import React from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { toast } from 'sonner'
import { motion } from 'framer-motion'

const SignupSchema = z.object({
  email: z.string().email("Invalid email address"),
  orgName: z.string().min(2, "Organization name too short"),
  password: z.string().min(8, "Password must be at least 8 characters"),
})

type SignupFormValues = z.infer<typeof SignupSchema>

export default function SignupPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = React.useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<SignupFormValues>({
    resolver: zodResolver(SignupSchema),
  })

  const { setAuth } = useAuthStore()

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true)
    try {
      const response = await api.post('/auth/signup', {
        email: data.email,
        password: data.password,
        org_name: data.orgName
      })
      
      const { user, access_token, refresh_token } = response.data
      setAuth(user, access_token, refresh_token)
      
      toast.success("Deployment successful. Welcome to the intelligence engine.")
      router.push('/dashboard')
    } catch (error: unknown) {
      const axiosErr = error as { response?: { data?: { detail?: string } } }
      const message = axiosErr.response?.data?.detail || "ERR_AUTH: Allocation failed or alias in use."
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="bg-[#000000] p-8 md:p-12 border border-[#333333] rounded-[6px]"
    >
      <div className="mb-10 flex flex-col gap-2">
        <h1 className="text-[24px] font-semibold text-[#EDEDED] tracking-tight leading-none mb-1">
          Deploy Tenant
        </h1>
        <p className="text-[13px] text-[#888888]">
          Initialize your secure data analysis environment.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        
        <div className="space-y-1.5 flex flex-col">
          <label className="text-[12px] font-medium text-[#EDEDED]">Organization Name</label>
          <div className="relative group">
            <input 
              {...register('orgName')} 
              className="w-full bg-[#111111] border border-[#333333] rounded-[4px] py-2 px-3 text-[14px] text-[#EDEDED] font-mono placeholder-[#888888] outline-none focus:border-[#EDEDED] transition-colors"
              placeholder="Acme Corp" 
              autoComplete="organization" 
            />
          </div>
          {errors.orgName && <p className="text-[11px] font-mono text-[#FF4444] mt-1">{errors.orgName.message}</p>}
        </div>

        <div className="space-y-1.5 flex flex-col">
          <label className="text-[12px] font-medium text-[#EDEDED]">Email</label>
          <div className="relative group">
            <input 
              {...register('email')} 
              type="email" 
              className="w-full bg-[#111111] border border-[#333333] rounded-[4px] py-2 px-3 text-[14px] text-[#EDEDED] font-mono placeholder-[#888888] outline-none focus:border-[#EDEDED] transition-colors"
              placeholder="user@domain.com" 
              autoComplete="email" 
            />
          </div>
          {errors.email && <p className="text-[11px] font-mono text-[#FF4444] mt-1">{errors.email.message}</p>}
        </div>

        <div className="space-y-1.5 flex flex-col">
          <label className="text-[12px] font-medium text-[#EDEDED]">Secure Password</label>
          <div className="relative group">
            <input 
              {...register('password')} 
              type="password" 
              className="w-full bg-[#111111] border border-[#333333] rounded-[4px] py-2 px-3 text-[14px] text-[#EDEDED] font-mono placeholder-[#888888] outline-none focus:border-[#EDEDED] transition-colors"
              placeholder="••••••••" 
              autoComplete="new-password" 
            />
          </div>
          {errors.password && <p className="text-[11px] font-mono text-[#FF4444] mt-1">{errors.password.message}</p>}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2.5 rounded-[4px] bg-[#EDEDED] text-[#000000] text-[13px] font-medium flex items-center justify-center gap-2 mt-4 hover:bg-[#CCCCCC] transition-colors disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Deploy <ArrowRight className="h-4 w-4" /></>}
        </button>
      </form>

      <p className="text-[11px] text-[#888888] mt-6 text-center">
        By continuing, you agree to our Terms of Intelligence & Isolation Protocol.
      </p>

      <div className="mt-8 pt-6 border-t border-[#333333] text-center">
        <p className="text-[12px] text-[#888888]">
          Already have an account?{' '}
          <Link href="/login" className="text-[#EDEDED] hover:underline underline-offset-2">
            Log In
          </Link>
        </p>
      </div>
    </motion.div>
  )
}
