import {registerRoot, Composition} from 'remotion';
import {Ad, adDuration} from './Ad';
import {Reel, reelDuration} from './Reel';
import {Soft, softDuration} from './Soft';
import {Motion, motionDuration} from './Motion';
import {Cine, cineDuration} from './Cine';
import {Pop, popDuration} from './Pop';
import {Alert, alertDuration} from './Alert';

const Root = () => (
  <>
    <Composition id="Ad" component={Ad} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: []}}
      calculateMetadata={({props}) => ({durationInFrames: adDuration(props.scenes)})} />
    <Composition id="Reel" component={Reel} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null}}
      calculateMetadata={({props}) => ({durationInFrames: reelDuration(props.scenes)})} />
    <Composition id="Soft" component={Soft} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null}}
      calculateMetadata={({props}) => ({durationInFrames: softDuration(props.scenes)})} />
    <Composition id="Motion" component={Motion} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null}}
      calculateMetadata={({props}) => ({durationInFrames: motionDuration(props.scenes)})} />
    <Composition id="Cine" component={Cine} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null}}
      calculateMetadata={({props}) => ({durationInFrames: cineDuration(props.scenes)})} />
    <Composition id="Pop" component={Pop} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null, sfx: {}, beat: 15}}
      calculateMetadata={({props}) => ({durationInFrames: popDuration(props.scenes)})} />
    <Composition id="Alert" component={Alert} fps={30} width={1080} height={1920}
      durationInFrames={450} defaultProps={{scenes: [], music: null, sfx: {}}}
      calculateMetadata={({props}) => ({durationInFrames: alertDuration(props.scenes)})} />
  </>
);
registerRoot(Root);
