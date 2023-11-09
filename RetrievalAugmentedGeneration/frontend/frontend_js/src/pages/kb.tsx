import Head from 'next/head'

import GradioPortal from '@/components/GradioPortal'

export default function Home() {
  return (
    <>
      <Head>
        <title>NVIDIA LLM Playground</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main>
        <GradioPortal src="/content/kb" />
      </main>
    </>
  )
}
