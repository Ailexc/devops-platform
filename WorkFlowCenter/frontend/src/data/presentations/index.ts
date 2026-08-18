import type { Scene } from '@/types/presentation'
import { sceneOverview } from './scene1-overview'
import { sceneProcess } from './scene2-demo'
import { sceneConfig } from './scene3-config'
import { sceneTaskPlatform } from './scene4-task-platform'
import { sceneIntegration } from './scene5-integration'
import { sceneDemo } from './scene6-demo'

export const scenes: Scene[] = [
  sceneOverview,
  sceneProcess,
  sceneConfig,
  sceneTaskPlatform,
  sceneIntegration,
  sceneDemo,
]

export function getSceneById(id: string): Scene | undefined {
  return scenes.find(s => s.id === id)
}

export function getSceneIndex(id: string): number {
  return scenes.findIndex(s => s.id === id)
}

export function getPrevScene(id: string): Scene | null {
  const idx = getSceneIndex(id)
  return idx > 0 ? scenes[idx - 1] : null
}

export function getNextScene(id: string): Scene | null {
  const idx = getSceneIndex(id)
  return idx < scenes.length - 1 ? scenes[idx + 1] : null
}
