import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import Loading from "../pages/Loading"

describe("Loading Component", () => {
  it("renders correctly with loading text", () => {
    render(<Loading />)
    expect(screen.getByText(/Loading Workspace.../i)).toBeInTheDocument()
  })
})
