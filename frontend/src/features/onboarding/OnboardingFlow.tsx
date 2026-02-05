import { useOnboardingStore } from '@/stores/onboardingStore'
import OnboardingLayout from './OnboardingLayout'
import WelcomeStep from './steps/WelcomeStep'
import BirthDataStep from './steps/BirthDataStep'
import CalculationStep from './steps/CalculationStep'
import GenesisStep from './steps/GenesisStep'
import { motion } from 'framer-motion'

export default function OnboardingFlow() {
    const { currentStep } = useOnboardingStore()

    // Step Map
    const renderStep = () => {
        switch (currentStep) {
            case 'welcome':
                return <WelcomeStep key="welcome" />
            case 'birth-data':
                return <BirthDataStep key="birth-data" />
            case 'calculation':
                return <CalculationStep key="calculation" />
            case 'genesis':
                return <GenesisStep key="genesis" />
            default:
                return <WelcomeStep key="default" />
        }
    }

    return (
        <OnboardingLayout>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full"
            >
                {renderStep()}
            </motion.div>
        </OnboardingLayout>
    )
}
