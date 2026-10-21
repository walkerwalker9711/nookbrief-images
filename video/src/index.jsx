import {registerRoot, Composition} from 'remotion';
import {Ad, adDuration} from './Ad';

const Root = () => (
  <Composition id="Ad" component={Ad} fps={30} width={1080} height={1920}
    durationInFrames={450} defaultProps={{scenes: []}}
    calculateMetadata={({props}) => ({durationInFrames: adDuration(props.scenes)})} />
);
registerRoot(Root);
