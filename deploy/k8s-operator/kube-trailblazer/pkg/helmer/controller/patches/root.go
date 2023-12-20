package chart

// NotRoot not root
func (ch *Chart) NotRoot() {
	ch.parent = nil
	ch.dependencies = nil
	ch.Metadata.Dependencies = nil
}
