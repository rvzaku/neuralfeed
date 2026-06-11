import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// next/navigation stubs shared by all component tests
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
