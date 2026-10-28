# Retain repository-settings authority

The existing admin repository designated Safe-Settings configuration as canonical but
never installed the App. Preserve that repository-settings authority while independently
reading GitHub state through official APIs. Keep organization membership/default and
Actions policies separately owned; any executor replacement must explicitly transfer
field ownership rather than introduce competing writers.
