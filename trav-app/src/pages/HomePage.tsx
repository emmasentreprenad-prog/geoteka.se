import tracksData from '../data/travbanor.json'
import type { Track } from '../types'
import { SwedenMap } from '../components/SwedenMap'
import { TrackSearchList } from '../components/TrackSearchList'
import { useCalendar } from '../hooks/useCalendar'

const tracks = tracksData as Track[]

export function HomePage() {
  const { nextRaceDate } = useCalendar()

  return (
    <div className="home-page">
      <SwedenMap tracks={tracks} nextRaceDate={nextRaceDate} />
      <TrackSearchList tracks={tracks} nextRaceDate={nextRaceDate} />
    </div>
  )
}
