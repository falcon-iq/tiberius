import { ReactNode } from "react"

interface MainWorkAreaProps {
  children: ReactNode
}

const MainWorkArea = ({ children }: MainWorkAreaProps) => {
  return (
    <main className="flex flex-1 flex-col overflow-hidden">
      {children}
    </main>
  )
}

export default MainWorkArea;