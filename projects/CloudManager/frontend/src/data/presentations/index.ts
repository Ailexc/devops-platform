import type { PresentationScene, SceneMeta } from '@/types/presentation'
import { scene1 } from './scene1-overview'
import { scene2 } from './scene2-resource'
import { scene3 } from './scene3-ticket'
import { scene4 } from './scene4-topology'
import { scene5 } from './scene5-cost'
import { scene6 } from './scene6-fullchain'

/** 所有演示场景 */
export const scenes: PresentationScene[] = [
  scene1,
  scene2,
  scene3,
  scene4,
  scene5,
  scene6,
]

/** 场景元数据（目录页使用） */
export const sceneMetas: SceneMeta[] = scenes.map(s => ({
  id: s.id,
  title: s.title,
  subtitle: s.subtitle,
  description: s.description,
  duration: s.duration,
  icon: s.icon,
  color: s.color,
  stepCount: s.steps.length,
}))

/** 根据 ID 获取场景 */
export function getScene(id: string): PresentationScene | undefined {
  return scenes.find(s => s.id === id)
}

/** 获取场景索引 */
export function getSceneIndex(id: string): number {
  return scenes.findIndex(s => s.id === id)
}
