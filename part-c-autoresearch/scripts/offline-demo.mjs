import { apply } from '../plugins/autoresearch.mjs'

const registered = []
const fakeContext = {
  tools: {
    register(tool) {
      registered.push(tool)
    },
  },
}

apply(fakeContext)
if (registered.length !== 1 || registered[0].name !== 'run_autoresearch_experiment') {
  throw new Error('The autoresearch tool was not registered correctly.')
}

const report = await registered[0].execute({ maxTrials: 5, seed: 7 })
if (!(report.best.validationMse < report.baseline.validationMse)) {
  throw new Error('The autoresearch loop did not improve on the baseline.')
}
if (report.trials.length !== 5) {
  throw new Error(`Expected five trials, got ${report.trials.length}.`)
}

console.log('Registered custom tool:', registered[0].name)
console.log(`Baseline validation MSE: ${report.baseline.validationMse}`)
console.log(`Best validation MSE: ${report.best.validationMse}`)
console.log(`Improvement: ${(report.improvement * 100).toFixed(2)}%`)
console.log(`Trials evaluated: ${report.trials.length}`)
console.log(`Artifact: ${report.artifactPath}`)
console.log('Offline Part C autoresearch demo passed.')
