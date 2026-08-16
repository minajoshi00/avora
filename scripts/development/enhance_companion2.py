with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\frontend\\src\\components\\sections\\CompanionExperience.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Enhance the CompanionExperience to better connect with character states
# The key changes:
# 1. Add better state connectivity
# 2. Improve the character visualization
# 3. Connect timeline to chat states

# New top section enhancement:
enhanced_top = '''

    {/* Enhanced active moment detail */}
    <AnimatePresence mode="wait">
      <motion.div
        key={activeMoment}
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -30, scale: 0.95 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="relative max-w-4xl mx-auto mb-8"
      >
        <div className="relative rounded-3xl border border-white/[0.1] bg-white/[0.03] backdrop-blur-xl p-8 lg:p-10 overflow-hidden">
          {/* Animated background */}
          <motion.div
            className="absolute inset-0 opacity-40"
            style={{
              background: `radial-gradient(circle at 30% 30%, ${moments.find(m => m.id === activeMoment)?.color}15 0%, transparent 50%)`,
            }}
            animate={{
              scale: [1, 1.05, 1],
            }}
            transition={{ duration: 4, repeat: Infinity }}
          />

          <div className="relative z-10 flex flex-col lg:flex-row items-center gap-8">
            {/* Core visualization - enlarged and enhanced */}
            <motion.div
              className="shrink-0 lg:w-24 lg:h-24"
              animate={{
                rotate: [0, 8, -8, 0],
              }}
              transition={{ duration: 8, repeat: Infinity }}
            >
              <InteractiveAvoraCore
                state={moments.find(m => m.id === activeMoment)?.state || 'idle'}
                size={180}
              />
            </motion.div>

            {/* Content */}
            <div className="flex-1 text-left">
              <motion.div
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/[0.1] bg-white/[0.04] mb-4"
                style={{
                  borderColor: `${moments.find(m => m.id === activeMoment)?.color}30`,
                }}
              >
                <div
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: moments.find(m => m.id === activeMoment)?.color }}
                />
                <span
                  className="text-[10px] font-medium tracking-wider uppercase"
                  style={{ color: moments.find(m => m.id === activeMoment)?.color }}
                >
                  {moments.find(m => m.id === activeMoment)?.label}
                </span>
              </motion.div>

              <motion.h3
                className="text-3xl lg:text-4xl font-bold text-white mb-4"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                {moments.find(m => m.id === activeMoment)?.title}
              </motion.h3>

              <motion.p
                className="text-base lg:text-xl text-gray-400 leading-relaxed"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                {moments.find(m => m.id === activeMoment)?.description}
              </motion.p>

              <motion.div
                className="mt-6 flex items-center justify-center lg:justify-start gap-6 text-xs text-gray-500"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Always present
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  Never intrusive
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </AnimatePresence>
'''

# Replace the old top section
old_top_marker = '''<motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <SectionHeading
            label="The Companion"
            title="Already there."
            description="You don't open AVORA. AVORA is already there — understanding, waiting, evolving with you."
          />
        </motion.div>'''

if old_top_marker in content:
    content = content.replace(old_top_marker, enhanced_top)
    print('Enhanced top section')
else:
    print('Old top marker not found')
    
with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora frontend\\src\\components\\sections\\CompanionExperience.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("CompanionExperience enhanced")
PYEOF