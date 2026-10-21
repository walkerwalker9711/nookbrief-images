import {registerRoot, Composition} from 'remotion';
import {Ad, adDuration} from './Ad';
import {Reel, reelDuration} from './Reel';
import {Soft, softDuration} from './Soft';

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
  </>
);
registerRoot(Root);
